import math
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from backend.models.ingestion_job import IngestionJob
from backend.models.source_record import SourceRecord
from backend.models.project import ResearchProject
from backend.adapters import get_adapter, ADAPTER_REGISTRY, list_supported_adapters
from backend.adapters.base import RawRecord
from backend.adapters.manual_import import ManualImportAdapter, ManualImportError
from backend.services.preprocessing_service import PreprocessingService

logger = structlog.get_logger(__name__)


class IngestionService:
    """
    Manages data ingestion pipelines, background job state, deduplication,
    batching, and manual file imports.
    """

    MAX_CONCURRENT_JOBS = 3
    STALE_HEARTBEAT_TIMEOUT_SECONDS = 120  # 2 minutes

    @classmethod
    async def create_job(
        cls,
        db: AsyncSession,
        project_id: str,
        source_type: str,
        config: Dict[str, Any],
    ) -> IngestionJob:
        """
        Validates project existence, concurrency limits, and source adapter validity,
        then instantiates and returns a queued IngestionJob.
        """
        # 1. Verify project exists
        proj_stmt = select(ResearchProject).where(
            ResearchProject.id == project_id,
            ResearchProject.deleted_at.is_(None),
        )
        project = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        # 2. Verify adapter exists or is reembed job
        clean_source = source_type.lower().strip()
        if clean_source not in ADAPTER_REGISTRY and clean_source != "reembed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported source_type '{source_type}'. Supported sources: {', '.join(list_supported_adapters())}, reembed",
            )

        if clean_source in ADAPTER_REGISTRY:
            adapter_cls = ADAPTER_REGISTRY[clean_source]
            from backend.config import get_settings
            app_settings = get_settings()
            if (
                getattr(adapter_cls, "tos_status", "open") == "restricted"
                and not app_settings.ENABLE_RESTRICTED_SOURCES
                and not config.get("mock_mode", False)
                and not app_settings.MOCK_DATA_MODE
                and app_settings.ENVIRONMENT not in ["test", "testing"]
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Source adapter '{source_type}' has restricted ToS status and is disabled by default. Enable it with ENABLE_RESTRICTED_SOURCES=true.",
                )


        # 3. Check concurrent active jobs limit (max 3)
        active_jobs_stmt = select(func.count(IngestionJob.id)).where(
            IngestionJob.project_id == project_id,
            IngestionJob.status.in_(["queued", "running"]),
        )
        active_count = (await db.execute(active_jobs_stmt)).scalar() or 0
        if active_count >= cls.MAX_CONCURRENT_JOBS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Project already has {active_count} active job(s). Maximum allowed concurrent jobs is {cls.MAX_CONCURRENT_JOBS}.",
            )

        # 4. Create IngestionJob record
        now = datetime.now(timezone.utc)
        job = IngestionJob(
            project_id=project_id,
            source_type=clean_source,
            status="queued",
            config=config,
            records_found=0,
            records_stored=0,
            last_heartbeat_at=now,
            started_at=now,
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        logger.info("ingestion_job_created", job_id=str(job.id), project_id=project_id, source=clean_source)
        return job

    @classmethod
    async def get_job(
        cls,
        db: AsyncSession,
        project_id: str,
        job_id: str,
    ) -> IngestionJob:
        """
        Retrieves job by ID for the given project, triggering a stale heartbeat check.
        """
        stmt = select(IngestionJob).where(
            IngestionJob.id == job_id,
            IngestionJob.project_id == project_id,
        )
        job = (await db.execute(stmt)).scalar_one_or_none()
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Ingestion job '{job_id}' not found for project '{project_id}'.",
            )

        # Watchdog: If running but heartbeat is older than 2 minutes, mark failed
        if job.status == "running" and job.last_heartbeat_at:
            heartbeat = job.last_heartbeat_at
            if heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            time_since_heartbeat = (datetime.now(timezone.utc) - heartbeat).total_seconds()
            if time_since_heartbeat > cls.STALE_HEARTBEAT_TIMEOUT_SECONDS:
                job.status = "failed"
                job.error_details = {
                    "error": f"Job watchdog: heartbeat lost for {int(time_since_heartbeat)}s (exceeded {cls.STALE_HEARTBEAT_TIMEOUT_SECONDS}s limit).",
                    "stale_heartbeat": True,
                }
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
                await db.refresh(job)
                logger.warn("ingestion_job_watchdog_timeout", job_id=job_id)

        return job

    @classmethod
    async def list_jobs(
        cls,
        db: AsyncSession,
        project_id: str,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[IngestionJob], int]:
        """
        Lists ingestion jobs for a project with status filtering and pagination.
        """
        filters = [IngestionJob.project_id == project_id]
        if status_filter:
            filters.append(IngestionJob.status == status_filter.lower().strip())

        count_stmt = select(func.count(IngestionJob.id)).where(and_(*filters))
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(IngestionJob)
            .where(and_(*filters))
            .order_by(IngestionJob.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        jobs = (await db.execute(stmt)).scalars().all()
        return list(jobs), total

    @classmethod
    async def cancel_job(
        cls,
        db: AsyncSession,
        project_id: str,
        job_id: str,
    ) -> IngestionJob:
        """
        Cancels a running or queued ingestion job.
        """
        job = await cls.get_job(db, project_id, job_id)
        if job.status in ["completed", "failed", "cancelled"]:
            return job

        job.status = "cancelled"
        job.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)

        logger.info("ingestion_job_cancelled", job_id=job_id, project_id=project_id)
        return job

    @classmethod
    async def import_manual_dataset(
        cls,
        db: AsyncSession,
        project_id: str,
        file_content: bytes,
        file_format: str = "csv",
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a synchronous manual dataset import (CSV or JSON), performing schema validation,
        preprocessing, batching, deduplication, and database insertion.
        """
        # 1. Verify project exists
        proj_stmt = select(ResearchProject).where(
            ResearchProject.id == project_id,
            ResearchProject.deleted_at.is_(None),
        )
        project = (await db.execute(proj_stmt)).scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID '{project_id}' not found.",
            )

        adapter = ManualImportAdapter()
        try:
            raw_records = await adapter.fetch({
                "file_content": file_content,
                "file_format": file_format,
            })
        except ManualImportError as mie:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"message": str(mie), "validation_errors": mie.errors},
            )

        # 2. Process records in batches of 500
        batch_size = 500
        records_accepted = 0
        records_skipped_duplicate = 0
        records_failed = 0
        validation_errors = []

        seen_in_batch_hashes = set()

        for batch_start in range(0, len(raw_records), batch_size):
            batch_raw = raw_records[batch_start:batch_start + batch_size]
            batch_to_insert: List[SourceRecord] = []

            for raw in batch_raw:
                try:
                    norm = adapter.normalize(raw)
                    dedup_hash = norm["dedup_hash"]

                    # Check within-file in-memory duplicates
                    if dedup_hash in seen_in_batch_hashes:
                        records_skipped_duplicate += 1
                        continue

                    # Check database duplicates for this project (ignore soft-deleted)
                    existing_stmt = select(SourceRecord).where(
                        SourceRecord.project_id == project_id,
                        SourceRecord.dedup_hash == dedup_hash,
                        SourceRecord.deleted_at.is_(None),
                    )
                    existing_record = (await db.execute(existing_stmt)).scalar_one_or_none()

                    if existing_record:
                        # Record duplicate & save alternate URL if different
                        records_skipped_duplicate += 1
                        if raw.source_url and raw.source_url != existing_record.source_url:
                            meta = dict(existing_record.metadata_json or {})
                            alt_urls = meta.get("alternate_urls", [])
                            if raw.source_url not in alt_urls:
                                alt_urls.append(raw.source_url)
                                meta["alternate_urls"] = alt_urls
                                existing_record.metadata_json = meta
                        continue

                    # Mark as seen
                    seen_in_batch_hashes.add(dedup_hash)

                    # Create SourceRecord
                    rec = SourceRecord(
                        project_id=project_id,
                        source_platform=norm["source_platform"],
                        source_url=norm["source_url"],
                        source_date=norm["source_date"],
                        raw_content=norm["raw_content"],
                        author_handle=norm["author_handle"],
                        collection_method="manual_import",
                        is_duplicate=False,
                        dedup_hash=dedup_hash,
                        metadata_json=norm["metadata_json"],
                        language=norm["language"],
                    )
                    batch_to_insert.append(rec)
                    records_accepted += 1

                except Exception as exc:
                    records_failed += 1
                    validation_errors.append(f"Failed to process record: {str(exc)}")

            if batch_to_insert:
                db.add_all(batch_to_insert)
                await db.commit()

        logger.info(
            "manual_import_completed",
            project_id=project_id,
            accepted=records_accepted,
            duplicates=records_skipped_duplicate,
            failed=records_failed,
        )

        return {
            "records_accepted": records_accepted,
            "records_skipped_duplicate": records_skipped_duplicate,
            "records_failed": records_failed,
            "validation_errors": validation_errors,
        }

import asyncio
from datetime import datetime, timezone
from typing import List, Optional, Callable
from sqlalchemy import select
import structlog
from backend.database import AsyncSessionLocal
from backend.models.ingestion_job import IngestionJob
from backend.models.source_record import SourceRecord
from backend.adapters import get_adapter

logger = structlog.get_logger(__name__)


class IngestionWorker:
    """
    Background worker that runs automated source adapter ingestion jobs,
    handling batching, heartbeat tracking, deduplication, and graceful cancellation.
    """

    BATCH_SIZE = 50
    session_factory: Callable = AsyncSessionLocal

    @classmethod
    async def run_job(cls, job_id: str, session_factory: Optional[Callable] = None):
        logger.info("ingestion_worker_started", job_id=job_id)
        maker = session_factory or cls.session_factory

        async with maker() as db:
            stmt = select(IngestionJob).where(IngestionJob.id == job_id)
            job = (await db.execute(stmt)).scalar_one_or_none()
            if not job:
                logger.error("ingestion_job_not_found", job_id=job_id)
                return

            if job.status == "cancelled":
                logger.info("ingestion_job_already_cancelled", job_id=job_id)
                return

            # Mark job as running
            now = datetime.now(timezone.utc)
            job.status = "running"
            job.last_heartbeat_at = now
            await db.commit()

            if job.source_type == "reembed":
                await cls._run_reembedding_job(db, job)
                return

            adapter = get_adapter(job.source_type)
            if not adapter:
                job.status = "failed"
                job.error_details = {"error": f"No adapter registered for source type '{job.source_type}'"}
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
                return

            try:
                # 1. Fetch records from adapter
                raw_records = await adapter.fetch(job.config or {})
                job.records_found = len(raw_records)
                job.last_heartbeat_at = datetime.now(timezone.utc)
                await db.commit()

                # 2. Process records in batches
                stored_count = 0
                seen_hashes = set()

                for batch_start in range(0, len(raw_records), cls.BATCH_SIZE):
                    # Check for external cancellation
                    await db.refresh(job)
                    if job.status == "cancelled":
                        logger.info("ingestion_job_cancelled_mid_execution", job_id=job_id)
                        job.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                        return

                    batch_raw = raw_records[batch_start:batch_start + cls.BATCH_SIZE]
                    batch_to_insert: List[SourceRecord] = []

                    for raw in batch_raw:
                        norm = adapter.normalize(raw)
                        dedup_hash = norm["dedup_hash"]

                        # Check within-batch in-memory duplicates
                        if dedup_hash in seen_hashes:
                            continue

                        # Check DB duplicates for this project
                        existing_stmt = select(SourceRecord).where(
                            SourceRecord.project_id == job.project_id,
                            SourceRecord.dedup_hash == dedup_hash,
                            SourceRecord.deleted_at.is_(None),
                        )
                        existing_record = (await db.execute(existing_stmt)).scalar_one_or_none()

                        if existing_record:
                            # Preserve alternate URL if different
                            if raw.source_url and raw.source_url != existing_record.source_url:
                                meta = dict(existing_record.metadata_json or {})
                                alt_urls = meta.get("alternate_urls", [])
                                if raw.source_url not in alt_urls:
                                    alt_urls.append(raw.source_url)
                                    meta["alternate_urls"] = alt_urls
                                    existing_record.metadata_json = meta
                            continue

                        seen_hashes.add(dedup_hash)

                        rec = SourceRecord(
                            project_id=job.project_id,
                            source_platform=norm["source_platform"],
                            source_url=norm["source_url"],
                            source_date=norm["source_date"],
                            raw_content=norm["raw_content"],
                            author_handle=norm["author_handle"],
                            collection_method=norm.get("collection_method", "automated_adapter"),
                            ingestion_job_id=job.id,
                            is_duplicate=False,
                            dedup_hash=dedup_hash,
                            metadata_json=norm["metadata_json"],
                            language=norm["language"],
                        )
                        batch_to_insert.append(rec)
                        stored_count += 1

                    if batch_to_insert:
                        db.add_all(batch_to_insert)

                    job.records_stored = stored_count
                    job.last_heartbeat_at = datetime.now(timezone.utc)
                    await db.commit()

                    # Yield briefly to async event loop
                    await asyncio.sleep(0.01)

                # 3. Mark completed
                job.status = "completed"
                job.completed_at = datetime.now(timezone.utc)
                job.last_heartbeat_at = datetime.now(timezone.utc)
                await db.commit()
                logger.info(
                    "ingestion_job_completed",
                    job_id=job_id,
                    found=job.records_found,
                    stored=job.records_stored,
                )

            except Exception as exc:
                logger.error("ingestion_job_failed", job_id=job_id, error=str(exc))
                job.status = "failed"
                job.error_details = {"error": str(exc), "error_type": type(exc).__name__}
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()

    @classmethod
    async def _run_reembedding_job(cls, db, job: IngestionJob):
        """
        Re-embeds all relevant evidence records where embedding is NULL, stale,
        or generated by an outdated embedding model.
        """
        from backend.gemini.client import get_gemini_client
        from backend.models.evidence_record import EvidenceRecord
        from backend.models.source_record import SourceRecord
        from sqlalchemy.orm import selectinload
        from sqlalchemy import or_

        gemini_client = get_gemini_client()
        target_model = gemini_client.embedding_model_name

        try:
            stmt = (
                select(EvidenceRecord)
                .options(selectinload(EvidenceRecord.source_record))
                .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
                .where(
                    SourceRecord.project_id == job.project_id,
                    SourceRecord.deleted_at.is_(None),
                    EvidenceRecord.is_relevant == True,
                    or_(
                        EvidenceRecord.embedding.is_(None),
                        EvidenceRecord.embedding_stale == True,
                        EvidenceRecord.embedding_model_version != target_model,
                    ),
                )
            )
            records = (await db.execute(stmt)).scalars().all()
            job.records_found = len(records)
            job.last_heartbeat_at = datetime.now(timezone.utc)
            await db.commit()

            stored_count = 0
            for record in records:
                await db.refresh(job)
                if job.status == "cancelled":
                    job.completed_at = datetime.now(timezone.utc)
                    await db.commit()
                    return

                embed_text = record.evidence_excerpt or (record.source_record.raw_content[:500] if record.source_record else "")
                if embed_text:
                    emb = await gemini_client.generate_embedding(embed_text)
                    record.embedding = emb
                    record.embedding_stale = False
                    record.embedding_model_version = target_model
                    stored_count += 1
                    job.records_stored = stored_count
                    job.last_heartbeat_at = datetime.now(timezone.utc)
                    await db.commit()

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()
            logger.info("reembedding_job_completed", job_id=str(job.id), reembedded=stored_count)

        except Exception as exc:
            logger.error("reembedding_job_failed", job_id=str(job.id), error=str(exc))
            job.status = "failed"
            job.error_details = {"error": str(exc), "error_type": type(exc).__name__}
            job.completed_at = datetime.now(timezone.utc)
            await db.commit()

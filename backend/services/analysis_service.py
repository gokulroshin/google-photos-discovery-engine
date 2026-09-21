import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from backend.models.model_run import ModelRun
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.project import ResearchProject
from backend.config import get_settings

logger = structlog.get_logger(__name__)


class AnalysisService:
    """
    Coordinates model runs, AI analysis jobs, evidence queries, and human review routing.
    """

    @classmethod
    async def create_analysis_run(
        cls,
        db: AsyncSession,
        project_id: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> ModelRun:
        """
        Validates project existence and checks for running analysis runs,
        then instantiates a new queued ModelRun.
        """
        # 1. Check project
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

        # 2. Check for active running/queued model run
        active_run_stmt = select(ModelRun).where(
            ModelRun.project_id == project_id,
            ModelRun.status.in_(["queued", "running"]),
        )
        active_run = (await db.execute(active_run_stmt)).scalar_one_or_none()
        if active_run:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An analysis run ({active_run.id}) is already currently {active_run.status}. Please wait or cancel it first.",
            )

        # 3. Count unanalyzed source records
        analyzed_subquery = select(EvidenceRecord.source_record_id).where(
            EvidenceRecord.source_record_id.is_not(None)
        )
        unanalyzed_stmt = select(func.count(SourceRecord.id)).where(
            SourceRecord.project_id == project_id,
            SourceRecord.deleted_at.is_(None),
            SourceRecord.id.not_in(analyzed_subquery),
        )
        total_unprocessed = (await db.execute(unanalyzed_stmt)).scalar() or 0

        settings = get_settings()
        now = datetime.now(timezone.utc)
        model_run = ModelRun(
            project_id=project_id,
            model_name=settings.GEMINI_MODEL,
            prompt_version="1.0.0",
            parameters=parameters or {},
            status="queued",
            records_total=total_unprocessed,
            records_success=0,
            records_failed=0,
            started_at=now,
        )
        db.add(model_run)
        await db.commit()
        await db.refresh(model_run)

        logger.info(
            "analysis_run_created",
            model_run_id=str(model_run.id),
            project_id=project_id,
            records_to_process=total_unprocessed,
        )
        return model_run

    @classmethod
    async def get_model_run(
        cls,
        db: AsyncSession,
        project_id: str,
        run_id: str,
    ) -> ModelRun:
        """Retrieves single model run detail."""
        stmt = select(ModelRun).where(
            ModelRun.id == run_id,
            ModelRun.project_id == project_id,
        )
        run = (await db.execute(stmt)).scalar_one_or_none()
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model run '{run_id}' not found for project '{project_id}'.",
            )
        return run

    @classmethod
    async def list_model_runs(
        cls,
        db: AsyncSession,
        project_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ModelRun], int]:
        """Lists model runs for a project."""
        count_stmt = select(func.count(ModelRun.id)).where(ModelRun.project_id == project_id)
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(ModelRun)
            .where(ModelRun.project_id == project_id)
            .order_by(ModelRun.started_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        runs = (await db.execute(stmt)).scalars().all()
        return list(runs), total

    @classmethod
    async def resume_model_run(
        cls,
        db: AsyncSession,
        project_id: str,
        run_id: str,
    ) -> ModelRun:
        """Resumes a paused model run."""
        run = await cls.get_model_run(db, project_id, run_id)
        if run.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume model run with status '{run.status}'. Only 'paused' runs can be resumed.",
            )

        run.status = "queued"
        run.error_log = None
        await db.commit()
        await db.refresh(run)
        return run

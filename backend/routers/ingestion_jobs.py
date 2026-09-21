import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.schemas.ingestion_job import (
    IngestionJobCreate,
    IngestionJobResponse,
    IngestionJobListResponse,
)
from backend.auth.dependencies import get_current_user
from backend.services.ingestion_service import IngestionService
from backend.workers.ingestion_worker import IngestionWorker

router = APIRouter(prefix="/projects/{project_id}/jobs", tags=["Ingestion Jobs"])


@router.post("", response_model=IngestionJobResponse, status_code=status.HTTP_201_CREATED)
async def create_ingestion_job(
    project_id: str,
    payload: IngestionJobCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates an asynchronous ingestion job using an automated source adapter (e.g. play_store, app_store, reddit, youtube, forum)
    and dispatches the worker task to the background queue.
    Enforces a strict maximum of 3 concurrent active jobs per project.
    """
    job = await IngestionService.create_job(
        db=db,
        project_id=project_id,
        source_type=payload.source_type,
        config=payload.config,
    )

    # Enqueue background task
    background_tasks.add_task(IngestionWorker.run_job, str(job.id))

    return IngestionJobResponse.model_validate(job)


@router.get("", response_model=IngestionJobListResponse)
async def list_ingestion_jobs(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (queued, running, completed, failed, cancelled)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists ingestion jobs for a research project with status filtering and pagination.
    """
    jobs, total = await IngestionService.list_jobs(
        db=db,
        project_id=project_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return IngestionJobListResponse(
        items=[IngestionJobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job(
    project_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves real-time status, progress metrics, and error logs for a specific ingestion job.
    Includes automated watchdog detection for stale heartbeats.
    """
    job = await IngestionService.get_job(db, project_id, job_id)
    return IngestionJobResponse.model_validate(job)


@router.delete("/{job_id}", response_model=IngestionJobResponse)
async def cancel_ingestion_job(
    project_id: str,
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Cancels a running or queued ingestion job.
    """
    job = await IngestionService.cancel_job(db, project_id, job_id)
    return IngestionJobResponse.model_validate(job)

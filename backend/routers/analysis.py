import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.schemas.model_run import (
    ModelRunCreate,
    ModelRunResponse,
)
from backend.auth.dependencies import get_current_user
from backend.services.analysis_service import AnalysisService
from backend.workers.analysis_worker import AnalysisWorker
from pydantic import BaseModel, Field
from typing import List


class ModelRunListResponse(BaseModel):
    items: List[ModelRunResponse]
    total: int
    page: int = 1
    page_size: int = 20
    total_pages: int = 1


router = APIRouter(prefix="/projects/{project_id}", tags=["Analysis & Model Runs"])


@router.post("/analyze", response_model=ModelRunResponse, status_code=status.HTTP_201_CREATED)
async def start_analysis_job(
    project_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[ModelRunCreate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Initiates an AI classification and evidence extraction job across all unanalyzed source records.
    Dispatches the worker in the background and returns a queued ModelRun record.
    Enforces that only one analysis run may execute per project at a time.
    """
    model_run = await AnalysisService.create_analysis_run(
        db=db,
        project_id=project_id,
        parameters=payload.parameters if payload else None,
    )

    # Enqueue background task
    background_tasks.add_task(AnalysisWorker.run_analysis_job, str(model_run.id))

    return ModelRunResponse.model_validate(model_run)


@router.get("/model-runs", response_model=ModelRunListResponse)
async def list_model_runs(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists historical and active AI model classification runs for the project.
    """
    runs, total = await AnalysisService.list_model_runs(
        db=db,
        project_id=project_id,
        page=page,
        page_size=page_size,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ModelRunListResponse(
        items=[ModelRunResponse.model_validate(r) for r in runs],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/model-runs/{run_id}", response_model=ModelRunResponse)
async def get_model_run(
    project_id: str,
    run_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves progress, status, and error logs for a specific model run.
    """
    run = await AnalysisService.get_model_run(db, project_id, run_id)
    return ModelRunResponse.model_validate(run)


@router.post("/model-runs/{run_id}/resume", response_model=ModelRunResponse)
async def resume_model_run(
    project_id: str,
    run_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Resumes a model run that was paused due to temporary Gemini API rate-limiting or outages.
    """
    run = await AnalysisService.resume_model_run(db, project_id, run_id)
    background_tasks.add_task(AnalysisWorker.run_analysis_job, str(run.id))
    return ModelRunResponse.model_validate(run)

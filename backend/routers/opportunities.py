from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.schemas.opportunity import (
    OpportunityAreaResponse,
    OpportunityAreaUpdate,
    OpportunityListResponse,
)
from backend.auth.dependencies import get_current_user
from backend.services.opportunity_service import OpportunityService

router = APIRouter(prefix="/projects/{project_id}/opportunities", tags=["Opportunity Areas"])


@router.post("", response_model=OpportunityListResponse, status_code=status.HTTP_201_CREATED)
async def generate_opportunities(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Synthesizes Opportunity Areas from the latest problem taxonomy, scoring each area on all 9 strategic dimensions.
    """
    opportunities = await OpportunityService.generate_opportunities(
        db=db,
        project_id=project_id,
    )
    return OpportunityListResponse(
        items=[OpportunityAreaResponse.model_validate(o) for o in opportunities],
        total=len(opportunities),
    )


@router.get("", response_model=OpportunityListResponse)
async def list_opportunities(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(draft|validated|rejected|speculative)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists all scored opportunity areas with 9-dimension ratings, reach estimates, and validation effort.
    """
    opportunities = await OpportunityService.list_opportunities(
        db=db,
        project_id=project_id,
        status_filter=status_filter,
    )
    return OpportunityListResponse(
        items=[OpportunityAreaResponse.model_validate(o) for o in opportunities],
        total=len(opportunities),
    )


@router.get("/{opportunity_id}", response_model=OpportunityAreaResponse)
async def get_opportunity(
    project_id: str,
    opportunity_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves complete metrics, scoring methodology, and analyst notes for a specific opportunity area.
    """
    opportunity = await OpportunityService.get_opportunity(
        db=db,
        project_id=project_id,
        opportunity_id=opportunity_id,
    )
    return OpportunityAreaResponse.model_validate(opportunity)


@router.patch("/{opportunity_id}", response_model=OpportunityAreaResponse)
async def update_opportunity(
    project_id: str,
    opportunity_id: str,
    payload: OpportunityAreaUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates opportunity scores or analyst notes.
    Enforces that 'analyst_notes' MUST be provided when manually modifying scores.
    """
    updated = await OpportunityService.update_opportunity(
        db=db,
        project_id=project_id,
        opportunity_id=opportunity_id,
        update_data=payload.model_dump(exclude_unset=True),
    )
    return OpportunityAreaResponse.model_validate(updated)

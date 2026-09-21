from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.user import User
from backend.schemas.taxonomy import (
    TaxonomyCategoryResponse,
    TaxonomyCategoryUpdate,
    TaxonomyListResponse,
)
from backend.auth.dependencies import get_current_user, require_admin
from backend.services.taxonomy_service import TaxonomyService

router = APIRouter(prefix="/projects/{project_id}/taxonomy", tags=["Problem Taxonomy"])


@router.post("/generate", response_model=TaxonomyListResponse, status_code=status.HTTP_200_OK)
async def generate_taxonomy(
    project_id: str,
    k_clusters: Optional[int] = Query(None, ge=3, le=15, description="Optional target cluster count (3-15)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Triggers semantic clustering and Gemini category synthesis over all validated evidence records,
    creating a new versioned problem taxonomy.
    """
    categories = await TaxonomyService.generate_taxonomy(
        db=db,
        project_id=project_id,
        k_clusters=k_clusters,
    )
    version = categories[0].version if categories else 1

    return TaxonomyListResponse(
        items=[TaxonomyCategoryResponse.model_validate(c) for c in categories],
        total=len(categories),
        version=version,
    )


@router.get("", response_model=TaxonomyListResponse)
async def list_taxonomy_categories(
    project_id: str,
    version: Optional[int] = Query(None, description="Optional taxonomy version (defaults to latest)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists taxonomy problem categories for the given project and version with aggregated evidence counts.
    """
    categories, total, ver = await TaxonomyService.list_categories(
        db=db,
        project_id=project_id,
        version=version,
    )
    return TaxonomyListResponse(
        items=[TaxonomyCategoryResponse.model_validate(c) for c in categories],
        total=total,
        version=ver,
    )


@router.get("/{category_id}", response_model=TaxonomyCategoryResponse)
async def get_taxonomy_category(
    project_id: str,
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full details for a single taxonomy category including representative excerpts and open questions.
    """
    category = await TaxonomyService.get_category(
        db=db,
        project_id=project_id,
        category_id=category_id,
    )
    return TaxonomyCategoryResponse.model_validate(category)


@router.patch("/{category_id}", response_model=TaxonomyCategoryResponse)
async def update_taxonomy_category(
    project_id: str,
    category_id: str,
    payload: TaxonomyCategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Allows researchers to update category definitions, adjust names, or record additional open questions.
    """
    updated = await TaxonomyService.update_category(
        db=db,
        project_id=project_id,
        category_id=category_id,
        update_data=payload.model_dump(exclude_unset=True),
    )
    return TaxonomyCategoryResponse.model_validate(updated)


@router.post("/merge", response_model=TaxonomyCategoryResponse)
async def merge_taxonomy_categories(
    project_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Merges multiple categories into a single unified taxonomy category.
    Admin role required.
    """
    source_ids = payload.get("source_category_ids", [])
    target_name = payload.get("target_category_name", "Merged Category")
    merged_definition = payload.get("merged_definition")

    merged = await TaxonomyService.merge_categories(
        db=db,
        project_id=project_id,
        source_category_ids=source_ids,
        target_name=target_name,
        merged_definition=merged_definition,
    )
    return TaxonomyCategoryResponse.model_validate(merged)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_taxonomy_category(
    project_id: str,
    category_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Deletes a taxonomy category.
    Admin role required.
    """
    await TaxonomyService.delete_category(db, project_id, category_id)


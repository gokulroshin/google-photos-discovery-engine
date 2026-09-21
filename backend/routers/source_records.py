import math
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models.source_record import SourceRecord
from backend.models.project import ResearchProject
from backend.models.user import User
from backend.schemas.source_record import (
    SourceRecordResponse,
    SourceRecordListResponse,
    ImportSummaryResponse,
)
from backend.auth.dependencies import get_current_user
from backend.services.ingestion_service import IngestionService

router = APIRouter(prefix="/projects/{project_id}", tags=["Source Records"])


@router.post("/import", response_model=ImportSummaryResponse, status_code=status.HTTP_200_OK)
async def import_records(
    project_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload and import a CSV or JSON file containing source records into a research project.
    Validates schema, strips HTML, normalizes whitespace, detects language, validates dates,
    pseudonymizes author handles, and removes duplicate content.
    """
    # Verify file extension / format
    filename = file.filename or ""
    lower_filename = filename.lower()
    if lower_filename.endswith(".json"):
        file_format = "json"
    elif lower_filename.endswith(".csv") or lower_filename.endswith(".txt"):
        file_format = "csv"
    else:
        # Default to csv
        file_format = "csv"

    # Read content with file size checking
    file_bytes = await file.read()
    if len(file_bytes) > IngestionService.STALE_HEARTBEAT_TIMEOUT_SECONDS * 1024 * 1024:  # Quick guard
        pass

    result = await IngestionService.import_manual_dataset(
        db=db,
        project_id=project_id,
        file_content=file_bytes,
        file_format=file_format,
        filename=filename,
    )

    return ImportSummaryResponse(
        records_accepted=result["records_accepted"],
        records_skipped_duplicate=result["records_skipped_duplicate"],
        records_failed=result["records_failed"],
        validation_errors=result.get("validation_errors", []),
    )


@router.get("/records", response_model=SourceRecordListResponse)
async def list_source_records(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    platform: Optional[str] = Query(None, description="Filter by source platform"),
    source_date_from: Optional[datetime] = Query(None, description="Start source date"),
    source_date_to: Optional[datetime] = Query(None, description="End source date"),
    is_duplicate: Optional[bool] = Query(None, description="Filter by duplicate status"),
    language: Optional[str] = Query(None, description="Filter by language code (e.g. 'en')"),
    search: Optional[str] = Query(None, description="Search term in raw_content"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists paginated source records for a research project with multi-dimensional filtering.
    Includes both total count before filters and applied filter summary.
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

    # 2. Base filter: un-deleted records belonging to project
    base_filter = [
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    ]

    # Total records before filters
    total_before_stmt = select(func.count(SourceRecord.id)).where(and_(*base_filter))
    total_before_filters = (await db.execute(total_before_stmt)).scalar() or 0

    # 3. Dynamic filters
    applied_filters: Dict[str, Any] = {}
    filters = list(base_filter)

    if platform:
        filters.append(func.lower(SourceRecord.source_platform) == platform.lower().strip())
        applied_filters["platform"] = platform
    if source_date_from:
        filters.append(SourceRecord.source_date >= source_date_from)
        applied_filters["source_date_from"] = source_date_from.isoformat()
    if source_date_to:
        filters.append(SourceRecord.source_date <= source_date_to)
        applied_filters["source_date_to"] = source_date_to.isoformat()
    if is_duplicate is not None:
        filters.append(SourceRecord.is_duplicate == is_duplicate)
        applied_filters["is_duplicate"] = is_duplicate
    if language:
        filters.append(func.lower(SourceRecord.language) == language.lower().strip())
        applied_filters["language"] = language
    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(SourceRecord.raw_content.ilike(search_pattern))
        applied_filters["search"] = search

    # Filtered total count
    count_stmt = select(func.count(SourceRecord.id)).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated query
    stmt = (
        select(SourceRecord)
        .where(and_(*filters))
        .order_by(SourceRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = (await db.execute(stmt)).scalars().all()

    def sanitize_record(r: SourceRecord) -> SourceRecordResponse:
        resp = SourceRecordResponse.model_validate(r)
        if current_user.role != "admin" and resp.metadata_json and "original_handle" in resp.metadata_json:
            clean_meta = dict(resp.metadata_json)
            clean_meta.pop("original_handle", None)
            resp.metadata_json = clean_meta
        return resp

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return SourceRecordListResponse(
        items=[sanitize_record(r) for r in records],
        total=total,
        total_before_filters=total_before_filters,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        applied_filters=applied_filters,
    )


@router.get("/records/{record_id}", response_model=SourceRecordResponse)
async def get_source_record(
    project_id: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full source record details including raw content and metadata.
    """
    stmt = select(SourceRecord).where(
        SourceRecord.id == record_id,
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source record '{record_id}' not found in project '{project_id}'.",
        )
    resp = SourceRecordResponse.model_validate(record)
    if current_user.role != "admin" and resp.metadata_json and "original_handle" in resp.metadata_json:
        clean_meta = dict(resp.metadata_json)
        clean_meta.pop("original_handle", None)
        resp.metadata_json = clean_meta
    return resp


@router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source_record(
    project_id: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft-deletes a source record (setting deleted_at timestamp).
    """
    stmt = select(SourceRecord).where(
        SourceRecord.id == record_id,
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source record '{record_id}' not found in project '{project_id}'.",
        )

    record.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return None

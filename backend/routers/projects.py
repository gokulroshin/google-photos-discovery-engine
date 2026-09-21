import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.ingestion_job import IngestionJob
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.opportunity_area import OpportunityArea
from backend.models.user import User
from backend.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectListResponse,
)
from backend.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/projects", tags=["Projects"])


async def _get_project_stats(db: AsyncSession, project_id: str):
    """Computes real-time record and evidence counts for a project."""
    record_count_stmt = select(func.count(SourceRecord.id)).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )
    evidence_count_stmt = select(func.count(EvidenceRecord.id)).join(
        SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
    ).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
        EvidenceRecord.is_relevant == True,
    )
    
    record_count = (await db.execute(record_count_stmt)).scalar() or 0
    evidence_count = (await db.execute(evidence_count_stmt)).scalar() or 0
    return record_count, evidence_count


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a new research project. Validates name uniqueness.
    """
    # Check if a project with the same name already exists
    stmt = select(ResearchProject).where(
        func.lower(ResearchProject.name) == func.lower(payload.name.strip()),
        ResearchProject.deleted_at.is_(None),
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A research project named '{payload.name}' already exists.",
        )

    project = ResearchProject(
        name=payload.name.strip(),
        description=payload.description,
        research_questions=payload.research_questions,
        status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        research_questions=project.research_questions or [],
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        record_count=0,
        evidence_count=0,
    )


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search term for project name or description"),
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(draft|active|archived)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists research projects with pagination and aggregate counts.
    """
    filters = [ResearchProject.deleted_at.is_(None)]
    if status_filter:
        filters.append(ResearchProject.status == status_filter)
    if search:
        search_term = f"%{search.strip()}%"
        filters.append(
            or_(
                ResearchProject.name.ilike(search_term),
                ResearchProject.description.ilike(search_term),
            )
        )

    # Total count
    count_stmt = select(func.count(ResearchProject.id)).where(and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated query
    stmt = (
        select(ResearchProject)
        .where(and_(*filters))
        .order_by(ResearchProject.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    projects = (await db.execute(stmt)).scalars().all()

    items = []
    for proj in projects:
        rec_count, ev_count = await _get_project_stats(db, str(proj.id))
        items.append(
            ProjectResponse(
                id=str(proj.id),
                name=proj.name,
                description=proj.description,
                research_questions=proj.research_questions or [],
                status=proj.status,
                created_at=proj.created_at,
                updated_at=proj.updated_at,
                record_count=rec_count,
                evidence_count=ev_count,
            )
        )

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return ProjectListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves detailed project metrics and status.
    """
    stmt = select(ResearchProject).where(
        ResearchProject.id == project_id,
        ResearchProject.deleted_at.is_(None),
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    rec_count, ev_count = await _get_project_stats(db, project_id)

    # Active jobs count
    jobs_stmt = select(func.count(IngestionJob.id)).where(
        IngestionJob.project_id == project_id,
        IngestionJob.status.in_(["queued", "running"]),
    )
    active_jobs = (await db.execute(jobs_stmt)).scalar() or 0

    # Categories count
    cat_stmt = select(func.count(TaxonomyCategory.id)).where(
        TaxonomyCategory.project_id == project_id
    )
    total_categories = (await db.execute(cat_stmt)).scalar() or 0

    # Opportunities count
    opp_stmt = select(func.count(OpportunityArea.id)).where(
        OpportunityArea.project_id == project_id
    )
    total_opportunities = (await db.execute(opp_stmt)).scalar() or 0

    return ProjectDetailResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        research_questions=project.research_questions or [],
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        record_count=rec_count,
        evidence_count=ev_count,
        active_jobs_count=active_jobs,
        total_categories_count=total_categories,
        total_opportunities_count=total_opportunities,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    payload: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Updates project metadata, status, or research questions.
    """
    stmt = select(ResearchProject).where(
        ResearchProject.id == project_id,
        ResearchProject.deleted_at.is_(None),
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    if payload.name and payload.name.strip() != project.name:
        # Check name collision
        name_check_stmt = select(ResearchProject).where(
            func.lower(ResearchProject.name) == func.lower(payload.name.strip()),
            ResearchProject.id != project_id,
            ResearchProject.deleted_at.is_(None),
        )
        existing = (await db.execute(name_check_stmt)).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Another project named '{payload.name}' already exists.",
            )
        project.name = payload.name.strip()

    if payload.description is not None:
        project.description = payload.description
    if payload.research_questions is not None:
        project.research_questions = payload.research_questions
    if payload.status is not None:
        project.status = payload.status

    project.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(project)

    rec_count, ev_count = await _get_project_stats(db, project_id)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        description=project.description,
        research_questions=project.research_questions or [],
        status=project.status,
        created_at=project.created_at,
        updated_at=project.updated_at,
        record_count=rec_count,
        evidence_count=ev_count,
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Soft-deletes a project. Blocked if there are active ingestion or analysis jobs.
    Admin role required.
    """
    stmt = select(ResearchProject).where(
        ResearchProject.id == project_id,
        ResearchProject.deleted_at.is_(None),
    )
    project = (await db.execute(stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with ID '{project_id}' not found.",
        )

    # Check for active running/queued jobs
    jobs_stmt = select(func.count(IngestionJob.id)).where(
        IngestionJob.project_id == project_id,
        IngestionJob.status.in_(["queued", "running"]),
    )
    active_jobs = (await db.execute(jobs_stmt)).scalar() or 0
    if active_jobs > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete project while {active_jobs} active job(s) are running or queued. Please cancel them first.",
        )

    # Soft delete
    project.deleted_at = datetime.now(timezone.utc)
    project.status = "archived"
    await db.commit()
    return None


@router.get("/{project_id}/stats")
async def get_project_stats(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Computes comprehensive statistics for the project overview dashboard:
    source diversity, confidence distribution, review queue depth, and active system alerts.
    """
    # 1. Project check
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

    # 2. Record counts
    total_records = (await db.execute(
        select(func.count(SourceRecord.id)).where(
            SourceRecord.project_id == project_id,
            SourceRecord.deleted_at.is_(None),
        )
    )).scalar() or 0

    # 3. Evidence counts & confidence
    evidence_stmt = select(EvidenceRecord).join(
        SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
    ).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
        EvidenceRecord.is_relevant == True,
    )
    evidence_records = (await db.execute(evidence_stmt)).scalars().all()
    total_evidence = len(evidence_records)

    # 4. Review queue depth
    review_queue_depth = sum(1 for e in evidence_records if e.needs_human_review)

    # 5. Source diversity
    platform_stmt = select(
        SourceRecord.source_platform, func.count(SourceRecord.id)
    ).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    ).group_by(SourceRecord.source_platform)
    platform_rows = (await db.execute(platform_stmt)).all()
    source_diversity = {row[0]: row[1] for row in platform_rows}

    # 6. Confidence distribution histogram
    confidence_bins = {
        "0.0-0.5 (Low)": 0,
        "0.5-0.7 (Moderate)": 0,
        "0.7-0.85 (High)": 0,
        "0.85-1.0 (Very High)": 0,
    }
    for e in evidence_records:
        score = e.confidence_score or 0.0
        if score < 0.5:
            confidence_bins["0.0-0.5 (Low)"] += 1
        elif score < 0.7:
            confidence_bins["0.5-0.7 (Moderate)"] += 1
        elif score < 0.85:
            confidence_bins["0.7-0.85 (High)"] += 1
        else:
            confidence_bins["0.85-1.0 (Very High)"] += 1

    # 7. Recent jobs
    recent_jobs_stmt = select(IngestionJob).where(
        IngestionJob.project_id == project_id
    ).order_by(IngestionJob.created_at.desc()).limit(5)
    recent_jobs = (await db.execute(recent_jobs_stmt)).scalars().all()

    # 8. Categories count & Opportunity count
    categories_count = (await db.execute(
        select(func.count(TaxonomyCategory.id)).where(TaxonomyCategory.project_id == project_id)
    )).scalar() or 0

    opportunities_count = (await db.execute(
        select(func.count(OpportunityArea.id)).where(OpportunityArea.project_id == project_id)
    )).scalar() or 0

    # 9. Active warnings
    active_jobs_count = (await db.execute(
        select(func.count(IngestionJob.id)).where(
            IngestionJob.project_id == project_id,
            IngestionJob.status.in_(["queued", "running"]),
        )
    )).scalar() or 0

    is_partial_dataset = active_jobs_count > 0 or total_records < 10
    has_pending_reviews = review_queue_depth > 0
    is_stale_taxonomy = categories_count == 0 and total_evidence > 10

    return {
        "project_id": project_id,
        "total_records": total_records,
        "total_evidence": total_evidence,
        "review_queue_depth": review_queue_depth,
        "categories_count": categories_count,
        "opportunities_count": opportunities_count,
        "source_diversity": source_diversity,
        "confidence_distribution": confidence_bins,
        "recent_jobs": [
            {
                "id": str(j.id),
                "job_type": j.job_type,
                "source_type": j.source_type,
                "status": j.status,
                "records_found": j.records_found,
                "records_stored": j.records_stored,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in recent_jobs
        ],
        "warnings": {
            "is_partial_dataset": is_partial_dataset,
            "has_pending_reviews": has_pending_reviews,
            "pending_reviews_count": review_queue_depth,
            "is_stale_taxonomy": is_stale_taxonomy,
        },
    }


@router.get("/{project_id}/storage")
async def get_project_storage_breakdown(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns storage utilization breakdown for a research project including
    source records size, evidence size, export files size, and total storage.
    """
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

    # 1. Source records metrics
    src_stmt = select(
        func.count(SourceRecord.id),
        func.coalesce(func.sum(func.length(SourceRecord.raw_content)), 0),
    ).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )
    src_res = (await db.execute(src_stmt)).first()
    source_count = src_res[0] or 0
    source_bytes = int(src_res[1] or 0)

    # 2. Evidence records metrics (including vector embedding storage: 768 floats * 4 bytes = 3,072 bytes per record)
    ev_stmt = select(
        func.count(EvidenceRecord.id),
        func.coalesce(func.sum(func.length(EvidenceRecord.evidence_excerpt)), 0) +
        func.coalesce(func.sum(func.length(EvidenceRecord.rationale)), 0),
    ).join(
        SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id
    ).where(
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )
    ev_res = (await db.execute(ev_stmt)).first()
    evidence_count = ev_res[0] or 0
    evidence_text_bytes = int(ev_res[1] or 0)
    embedding_bytes = evidence_count * (768 * 4)  # 3072 bytes per pgvector 768-dim float32 vector
    evidence_total_bytes = evidence_text_bytes + embedding_bytes

    # 3. Reports metrics
    from backend.models.report import ResearchReport
    rpt_stmt = select(
        func.count(ResearchReport.id),
        func.coalesce(func.sum(func.length(ResearchReport.markdown_content)), 0),
    ).where(
        ResearchReport.project_id == project_id,
    )
    rpt_res = (await db.execute(rpt_stmt)).first()
    reports_count = rpt_res[0] or 0
    reports_bytes = int(rpt_res[1] or 0)

    # 4. Exports estimate (CSV / JSON exports)
    export_files_bytes = int(source_bytes * 0.8 + evidence_total_bytes * 0.5)

    total_bytes = source_bytes + evidence_total_bytes + reports_bytes + export_files_bytes

    def format_bytes(b: int) -> str:
        if b < 1024:
            return f"{b} B"
        elif b < 1024 * 1024:
            return f"{b / 1024:.1f} KB"
        elif b < 1024 * 1024 * 1024:
            return f"{b / (1024 * 1024):.2f} MB"
        return f"{b / (1024 * 1024 * 1024):.2f} GB"

    return {
        "project_id": project_id,
        "total_bytes": total_bytes,
        "total_formatted": format_bytes(total_bytes),
        "breakdown": {
            "source_records": {
                "count": source_count,
                "bytes": source_bytes,
                "formatted": format_bytes(source_bytes),
            },
            "evidence_records": {
                "count": evidence_count,
                "bytes": evidence_total_bytes,
                "text_bytes": evidence_text_bytes,
                "vector_embedding_bytes": embedding_bytes,
                "formatted": format_bytes(evidence_total_bytes),
            },
            "reports": {
                "count": reports_count,
                "bytes": reports_bytes,
                "formatted": format_bytes(reports_bytes),
            },
            "export_files": {
                "estimated_bytes": export_files_bytes,
                "formatted": format_bytes(export_files_bytes),
            },
        },
    }



import math
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.database import get_db
from backend.models.evidence_record import EvidenceRecord
from backend.models.source_record import SourceRecord
from backend.models.model_run import ModelRun
from backend.models.project import ResearchProject
from backend.models.user import User
from backend.schemas.evidence_record import (
    EvidenceRecordResponse,
    EvidenceRecordDetailResponse,
    EvidenceRecordListResponse,
)
from backend.schemas.source_record import SourceRecordResponse
from backend.auth.dependencies import get_current_user, require_admin

router = APIRouter(prefix="/projects/{project_id}/evidence", tags=["Evidence Records"])



@router.get("", response_model=EvidenceRecordListResponse)
async def list_evidence_records(
    project_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    scenario: Optional[str] = Query(None, description="Filter by retrieval scenario"),
    outcome: Optional[str] = Query(None, description="Filter by retrieval outcome"),
    confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum confidence score"),
    confidence_max: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum confidence score"),
    label: Optional[str] = Query(None, description="Filter by relevance label tag"),
    needs_review: Optional[bool] = Query(None, description="Filter by human review requirement"),
    failure_point: Optional[str] = Query(None, description="Filter by specific failure point"),
    is_relevant: Optional[bool] = Query(True, description="Filter by relevance (default: True)"),
    search: Optional[str] = Query(None, description="Search in scenario, excerpt, or rationale"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists paginated evidence records for a research project with multi-dimensional filtering.
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

    # 2. Base query joined with un-deleted source records
    base_join_condition = and_(
        EvidenceRecord.source_record_id == SourceRecord.id,
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
    )

    # Total before dynamic filters
    total_before_stmt = select(func.count(EvidenceRecord.id)).join(SourceRecord, base_join_condition)
    total_before_filters = (await db.execute(total_before_stmt)).scalar() or 0

    # 3. Dynamic filters
    applied_filters: Dict[str, Any] = {}
    filters = [base_join_condition]

    if is_relevant is not None:
        filters.append(EvidenceRecord.is_relevant == is_relevant)
        applied_filters["is_relevant"] = is_relevant

    if outcome:
        filters.append(func.lower(EvidenceRecord.retrieval_outcome) == outcome.lower().strip())
        applied_filters["outcome"] = outcome

    if confidence_min is not None:
        filters.append(EvidenceRecord.confidence_score >= confidence_min)
        applied_filters["confidence_min"] = confidence_min

    if confidence_max is not None:
        filters.append(EvidenceRecord.confidence_score <= confidence_max)
        applied_filters["confidence_max"] = confidence_max

    if needs_review is not None:
        filters.append(EvidenceRecord.needs_human_review == needs_review)
        applied_filters["needs_review"] = needs_review

    if scenario:
        filters.append(EvidenceRecord.retrieval_scenario.ilike(f"%{scenario.strip()}%"))
        applied_filters["scenario"] = scenario

    if label:
        filters.append(EvidenceRecord.relevance_labels.contains([label.strip()]))
        applied_filters["label"] = label

    if failure_point:
        filters.append(EvidenceRecord.failure_points.contains([failure_point.strip()]))
        applied_filters["failure_point"] = failure_point

    if search:
        search_pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                EvidenceRecord.retrieval_scenario.ilike(search_pattern),
                EvidenceRecord.evidence_excerpt.ilike(search_pattern),
                EvidenceRecord.rationale.ilike(search_pattern),
                SourceRecord.raw_content.ilike(search_pattern),
            )
        )
        applied_filters["search"] = search

    # Filtered total count
    count_stmt = select(func.count(EvidenceRecord.id)).join(SourceRecord, and_(*filters))
    total = (await db.execute(count_stmt)).scalar() or 0

    # Paginated query
    stmt = (
        select(EvidenceRecord)
        .join(SourceRecord, and_(*filters))
        .order_by(EvidenceRecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = (await db.execute(stmt)).scalars().all()

    total_pages = math.ceil(total / page_size) if total > 0 else 1

    return EvidenceRecordListResponse(
        items=[EvidenceRecordResponse.model_validate(r) for r in records],
        total=total,
        total_before_filters=total_before_filters,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        applied_filters=applied_filters,
    )


@router.get("/search")
async def search_evidence_records(
    project_id: str,
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    min_similarity: float = Query(0.65, ge=0.0, le=1.0, description="Minimum similarity threshold (default: 0.65)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Semantic vector search over evidence records using text-embedding-004 embeddings,
    with cosine similarity ranking, low confidence fallbacks, and keyword fallback.
    """
    from backend.gemini.client import get_gemini_client

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

    base_join = and_(
        EvidenceRecord.source_record_id == SourceRecord.id,
        SourceRecord.project_id == project_id,
        SourceRecord.deleted_at.is_(None),
        EvidenceRecord.is_relevant == True,
    )

    # 2. Fetch all relevant evidence records for the project
    stmt = (
        select(EvidenceRecord)
        .options(selectinload(EvidenceRecord.source_record))
        .join(SourceRecord, base_join)
    )
    all_records = (await db.execute(stmt)).scalars().all()

    # 3. Generate embedding for query
    gemini_client = get_gemini_client()
    query_vector = await gemini_client.generate_embedding(q)

    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    # 4. Filter records with embeddings and compute cosine similarity
    scored_records: List[tuple[EvidenceRecord, float]] = []
    for rec in all_records:
        if rec.embedding and isinstance(rec.embedding, (list, tuple)):
            sim = cosine_similarity(query_vector, list(rec.embedding))
            scored_records.append((rec, sim))

    scored_records.sort(key=lambda x: x[1], reverse=True)

    is_low_confidence = False
    final_matches: List[tuple[EvidenceRecord, float]] = []

    if scored_records:
        # Check threshold
        above_threshold = [item for item in scored_records if item[1] >= min_similarity]
        if above_threshold:
            final_matches = above_threshold[:limit]
        else:
            # Zero results above threshold -> Return top-3 nearest with low_confidence=True
            final_matches = scored_records[:3]
            is_low_confidence = True
    else:
        # 5. Keyword search fallback when no records have embeddings
        search_terms = q.strip().split()
        search_pattern = f"%{q.strip()}%"

        kw_stmt = (
            select(EvidenceRecord)
            .options(selectinload(EvidenceRecord.source_record))
            .join(SourceRecord, base_join)
            .where(
                or_(
                    EvidenceRecord.retrieval_scenario.ilike(search_pattern),
                    EvidenceRecord.evidence_excerpt.ilike(search_pattern),
                    EvidenceRecord.rationale.ilike(search_pattern),
                    EvidenceRecord.missing_information.ilike(search_pattern),
                    SourceRecord.raw_content.ilike(search_pattern),
                    *[EvidenceRecord.failure_points.contains([t]) for t in search_terms if len(t) > 3],
                )
            )
            .limit(limit)
        )
        kw_records = (await db.execute(kw_stmt)).scalars().all()
        for idx, r in enumerate(kw_records):
            sim = 0.85 - (idx * 0.05)
            final_matches.append((r, max(0.4, sim)))

        if not final_matches:
            # Fallback to top-3 highest confidence records
            fallback_stmt = (
                select(EvidenceRecord)
                .options(selectinload(EvidenceRecord.source_record))
                .join(SourceRecord, base_join)
                .order_by(EvidenceRecord.confidence_score.desc())
                .limit(3)
            )
            fb_records = (await db.execute(fallback_stmt)).scalars().all()
            for idx, r in enumerate(fb_records):
                final_matches.append((r, 0.45 - (idx * 0.05)))
            is_low_confidence = True

    results = []
    for r, score in final_matches:
        item_dict = EvidenceRecordResponse.model_validate(r).model_dump()
        item_dict["similarity_score"] = round(score, 4)
        item_dict["is_low_confidence"] = is_low_confidence
        item_dict["source_platform"] = r.source_record.source_platform if r.source_record else "unknown"
        item_dict["raw_content"] = r.source_record.raw_content if r.source_record else ""
        results.append(item_dict)

    return {
        "query": q,
        "total_matches": len(results),
        "is_low_confidence": is_low_confidence,
        "min_similarity": min_similarity,
        "items": results,
    }


@router.post("/review/bulk")
async def bulk_review_evidence(
    project_id: str,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Bulk approves or rejects a batch of evidence records in the human review queue.
    """
    evidence_ids = payload.get("evidence_record_ids", [])
    action = payload.get("action", "approved")
    reviewer_notes = payload.get("reviewer_notes", "Bulk action")

    if not evidence_ids:
        raise HTTPException(status_code=400, detail="No evidence record IDs provided.")

    from backend.models.human_review import HumanReview

    processed = 0
    for ev_id in evidence_ids:
        stmt = (
            select(EvidenceRecord)
            .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
            .where(
                EvidenceRecord.id == ev_id,
                SourceRecord.project_id == project_id,
            )
        )
        rec = (await db.execute(stmt)).scalar_one_or_none()
        if rec:
            rec.needs_human_review = False
            if action == "rejected":
                rec.is_relevant = False

            review = HumanReview(
                evidence_record_id=rec.id,
                reviewer_id=str(current_user.id),
                action=action,
                reviewer_notes=reviewer_notes,
            )
            db.add(review)
            processed += 1

    await db.commit()
    return {"status": "success", "processed_count": processed, "action": action}


@router.post("/{evidence_id}/review", response_model=EvidenceRecordResponse)
async def review_evidence_record(
    project_id: str,
    evidence_id: str,
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submits a researcher review decision (approved, corrected, rejected) for an evidence record.
    """
    stmt = (
        select(EvidenceRecord)
        .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
        .where(
            EvidenceRecord.id == evidence_id,
            SourceRecord.project_id == project_id,
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence record '{evidence_id}' not found.",
        )

    from backend.models.human_review import HumanReview

    action = payload.get("action", "approved")
    corrections = payload.get("corrections", {})
    notes = payload.get("reviewer_notes")

    record.needs_human_review = False
    if action == "rejected":
        record.is_relevant = False
    elif action == "corrected" and corrections:
        for k, v in corrections.items():
            if hasattr(record, k) and v is not None:
                setattr(record, k, v)

    review = HumanReview(
        evidence_record_id=record.id,
        reviewer_id=str(current_user.id),
        action=action,
        corrections=corrections if action == "corrected" else None,
        reviewer_notes=notes,
    )
    db.add(review)
    await db.commit()
    await db.refresh(record)

    return EvidenceRecordResponse.model_validate(record)


@router.get("/{evidence_id}", response_model=EvidenceRecordDetailResponse)
async def get_evidence_record(
    project_id: str,
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves complete evidence record with full original raw content, source metadata,
    and model run provenance.
    """
    stmt = (
        select(EvidenceRecord)
        .options(selectinload(EvidenceRecord.source_record), selectinload(EvidenceRecord.model_run))
        .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
        .where(
            EvidenceRecord.id == evidence_id,
            SourceRecord.project_id == project_id,
            SourceRecord.deleted_at.is_(None),
        )
    )
    record = (await db.execute(stmt)).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evidence record '{evidence_id}' not found in project '{project_id}'.",
        )

    source_resp = SourceRecordResponse.model_validate(record.source_record) if record.source_record else None
    if source_resp and current_user.role != "admin" and source_resp.metadata_json and "original_handle" in source_resp.metadata_json:
        clean_meta = dict(source_resp.metadata_json)
        clean_meta.pop("original_handle", None)
        source_resp.metadata_json = clean_meta

    model_name = record.model_run.model_name if record.model_run else "gemini-1.5-pro"
    prompt_version = record.model_run.prompt_version if record.model_run else "1.0.0"

    resp = EvidenceRecordDetailResponse.model_validate(record)
    resp.source_record = source_resp
    resp.model_name = model_name
    resp.prompt_version = prompt_version
    return resp


@router.delete("/bulk", status_code=status.HTTP_200_OK)
async def delete_evidence_bulk(
    project_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Bulk soft-deletes evidence records.
    Admin role required.
    """
    evidence_ids: List[str] = payload.get("evidence_record_ids", [])
    if not evidence_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No evidence_record_ids provided.",
        )

    # Fetch matching evidence records within project
    stmt = (
        select(EvidenceRecord)
        .join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id)
        .where(
            EvidenceRecord.id.in_(evidence_ids),
            SourceRecord.project_id == project_id,
        )
    )
    records = list((await db.execute(stmt)).scalars().all())

    for r in records:
        r.is_relevant = False

    await db.commit()
    return {
        "status": "success",
        "deleted_count": len(records),
    }


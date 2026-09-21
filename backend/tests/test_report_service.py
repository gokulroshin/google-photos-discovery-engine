import pytest
import uuid
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.opportunity_area import OpportunityArea
from backend.models.ingestion_job import IngestionJob
from backend.services.report_service import ReportService


@pytest.mark.asyncio
async def test_report_generation_requires_minimum_10_records(db_session: AsyncSession):
    # Create project
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="Test Min Records Project",
        description="Testing 10 records requirement",
        research_questions=["What fails?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Add only 5 evidence records
    for i in range(5):
        src = SourceRecord(
            id=f"src_min_{i}",
            project_id=project.id,
            source_platform="reddit",
            raw_content=f"Lost photos of event {i}",
            author_handle=f"user_min_{i}",
            dedup_hash=f"hash_min_{i}",
        )
        db_session.add(src)
        await db_session.commit()

        ev = EvidenceRecord(
            id=str(uuid.uuid4()),
            source_record_id=src.id,
            is_relevant=True,
            evidence_excerpt=f"Lost photos of event {i}",
            confidence_score=0.85,
        )
        db_session.add(ev)
    await db_session.commit()

    # Attempt to generate report -> should raise 400
    with pytest.raises(HTTPException) as exc_info:
        await ReportService.generate_report(db=db_session, project_id=project.id)
    assert exc_info.value.status_code == 400
    assert "At least 10 relevant evidence records are required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_report_generation_blocked_when_job_running(db_session: AsyncSession):
    # Create project
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="Test Running Job Project",
        description="Testing job running lock",
        research_questions=["What fails?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Add 12 evidence records
    for i in range(12):
        src = SourceRecord(
            id=f"src_run_{i}",
            project_id=project.id,
            source_platform="play_store",
            raw_content=f"Cannot find receipt image {i}",
            author_handle=f"user_run_{i}",
            dedup_hash=f"hash_run_{i}",
        )
        db_session.add(src)
        await db_session.commit()

        ev = EvidenceRecord(
            id=str(uuid.uuid4()),
            source_record_id=src.id,
            is_relevant=True,
            evidence_excerpt=f"Cannot find receipt image {i}",
            confidence_score=0.88,
        )
        db_session.add(ev)
    await db_session.commit()

    # Add an active running ingestion job
    job = IngestionJob(
        id=str(uuid.uuid4()),
        project_id=project.id,
        source_type="play_store",
        status="running",
    )
    db_session.add(job)
    await db_session.commit()


    # Attempt to generate report -> should raise 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await ReportService.generate_report(db=db_session, project_id=project.id)
    assert exc_info.value.status_code == 409
    assert "Cannot generate report while analysis or ingestion job is running" in exc_info.value.detail


@pytest.mark.asyncio
async def test_report_generation_success_and_citation_validation(db_session: AsyncSession):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="Test Success Report Project",
        description="Comprehensive project report test",
        research_questions=["How do visual queries fail?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Add 15 source and evidence records
    for i in range(15):
        src = SourceRecord(
            id=f"src_success_{i}",
            project_id=project.id,
            source_platform="reddit" if i % 2 == 0 else "app_store",
            raw_content=f"Searching for red hat on beach #{i}",
            author_handle=f"user_success_{i}",
            dedup_hash=f"hash_success_{i}",
        )
        db_session.add(src)
        await db_session.commit()

        ev = EvidenceRecord(
            id=str(uuid.uuid4()),
            source_record_id=src.id,
            is_relevant=True,
            evidence_excerpt=f"Searching for red hat on beach #{i}",
            confidence_score=0.90 if i > 2 else 0.55,
            needs_human_review=(i <= 2),  # 3 pending reviews
        )
        db_session.add(ev)
    await db_session.commit()

    # Add category and opportunity
    cat = TaxonomyCategory(
        id=str(uuid.uuid4()),
        project_id=project.id,
        version=1,
        name="Multi-Attribute Breakdown",
        definition="Failure to intersect multiple visual attributes",
        user_segment="Family Archivists",
        failure_mechanism="Disjunctive keyword ranking",
        evidence_count=15,
        unique_author_count=15,
        confidence_level="high",
        representative_excerpts=["Searching for red hat on beach #0"],
    )
    db_session.add(cat)

    opp = OpportunityArea(
        id=str(uuid.uuid4()),
        project_id=project.id,
        name="Visual Entity Conjunction Ranking",
        description="Intersection score boost for multi-attribute queries",
        user_impact_score=8.5,
        strategic_relevance=9.0,
        problem_clarity=8.0,
        abandonment_rate=0.35,
        validation_effort="medium",
        potential_reach="High",
        scoring_methodology="High impact user friction",
        status="validated",
    )
    db_session.add(opp)
    await db_session.commit()

    # Generate report
    report = await ReportService.generate_report(
        db=db_session,
        project_id=project.id,
        is_partial=True,
    )

    assert report is not None
    assert report.id is not None
    assert report.evidence_count == 15
    assert report.pending_reviews_count == 3
    assert "⚠️ **Warning: Partial Dataset**" in report.markdown_content
    assert "⚠️ **Warning: Pending Human Reviews**" in report.markdown_content
    assert "Multi-Attribute Breakdown" in report.markdown_content
    assert "Visual Entity Conjunction Ranking" in report.markdown_content

    # Citation validation check: cited source ids should exist
    assert "src_success_" in report.markdown_content

    # List reports
    reports = await ReportService.list_reports(db=db_session, project_id=project.id)
    assert len(reports) >= 1
    assert reports[0].id == report.id

    # Get single report
    fetched = await ReportService.get_report(db=db_session, project_id=project.id, report_id=report.id)
    assert fetched.id == report.id


def test_citation_validator_unsupported_tagging():
    valid_ids = {"src_001", "src_002"}
    text_with_citations = "User reported failure [src_001] while another claimed [src_999] was broken."
    validated = ReportService._validate_citations(text_with_citations, valid_ids)
    assert "[src_001]" in validated
    assert "[src_999 — UNSUPPORTED — VERIFY]" in validated

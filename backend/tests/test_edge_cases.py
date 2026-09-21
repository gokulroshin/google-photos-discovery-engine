import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.model_run import ModelRun
from backend.models.ingestion_job import IngestionJob
from backend.workers.analysis_worker import AnalysisWorker
from backend.gemini.client import GeminiUnavailableError


@pytest.mark.asyncio
async def test_report_generation_blocked_when_analysis_job_running(
    client: AsyncClient,
    db_session: AsyncSession,
    researcher_headers: dict,
):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name=f"Edge Case Proj {uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Create an active running model run / analysis job
    active_run = ModelRun(
        project_id=project.id,
        model_name="gemini-1.5-pro",
        prompt_version="1.0.0",
        status="running",
    )
    db_session.add(active_run)
    await db_session.commit()

    # Attempt report generation -> should return 409 Conflict
    res = await client.post(
        f"/v1/projects/{project.id}/reports",
        headers=researcher_headers,
    )
    assert res.status_code == 409
    assert "running" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_analysis_job_idempotent_skips_classified_records():
    from backend.tests.conftest import TestAsyncSessionLocal

    async with TestAsyncSessionLocal() as db_session:
        project = ResearchProject(
            id=str(uuid.uuid4()),
            name=f"Idempotent Proj {uuid.uuid4().hex[:6]}",
            status="active",
        )
        db_session.add(project)
        await db_session.commit()

        # Create source record
        src = SourceRecord(
            id=f"src_idemp_{uuid.uuid4().hex[:6]}",
            project_id=project.id,
            source_platform="reddit",
            raw_content="Searched for my dog photo in Chicago.",
            dedup_hash=f"hash_{uuid.uuid4().hex[:6]}",
        )
        db_session.add(src)
        await db_session.commit()

        # Already has an evidence record
        ev = EvidenceRecord(
            id=str(uuid.uuid4()),
            source_record_id=src.id,
            is_relevant=True,
            confidence_score=0.9,
        )
        db_session.add(ev)
        await db_session.commit()

        # Create a model run
        model_run = ModelRun(
            project_id=project.id,
            model_name="gemini-1.5-pro",
            prompt_version="1.0.0",
            status="queued",
        )
        db_session.add(model_run)
        await db_session.commit()
        run_id = str(model_run.id)

    # Run analysis worker with TestAsyncSessionLocal
    await AnalysisWorker.run_analysis_job(run_id, session_factory=TestAsyncSessionLocal)

    async with TestAsyncSessionLocal() as db_session:
        stmt = select(ModelRun).where(ModelRun.id == run_id)
        refreshed_run = (await db_session.execute(stmt)).scalar_one()
        assert refreshed_run.status == "completed"
        # Unprocessed records total should be 0 because the record was already classified
        assert refreshed_run.records_total == 0


@pytest.mark.asyncio
async def test_project_storage_breakdown_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
    researcher_headers: dict,
):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name=f"Storage Test Proj {uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    src = SourceRecord(
        id=f"src_st_{uuid.uuid4().hex[:6]}",
        project_id=project.id,
        source_platform="reddit",
        raw_content="Testing storage size calculations in research discovery.",
        dedup_hash=f"hash_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(src)
    await db_session.commit()

    ev = EvidenceRecord(
        id=str(uuid.uuid4()),
        source_record_id=src.id,
        is_relevant=True,
        evidence_excerpt="storage size calculations",
        rationale="Clear memory failure context",
        confidence_score=0.9,
    )
    db_session.add(ev)
    await db_session.commit()

    res = await client.get(
        f"/v1/projects/{project.id}/storage",
        headers=researcher_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project.id
    assert data["total_bytes"] > 0
    assert "source_records" in data["breakdown"]
    assert "evidence_records" in data["breakdown"]
    assert data["breakdown"]["source_records"]["count"] == 1
    assert data["breakdown"]["evidence_records"]["count"] == 1

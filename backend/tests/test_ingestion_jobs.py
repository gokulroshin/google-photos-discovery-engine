import pytest
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException
from backend.services.ingestion_service import IngestionService
from backend.models.project import ResearchProject
from backend.models.ingestion_job import IngestionJob
from backend.workers.ingestion_worker import IngestionWorker
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_create_ingestion_job_success(db_session):
    project = ResearchProject(name=f"Job Test Project {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    job = await IngestionService.create_job(
        db=db_session,
        project_id=str(project.id),
        source_type="play_store",
        config={"limit": 10, "mock_mode": True},
    )

    assert job.id is not None
    assert job.status == "queued"
    assert job.project_id == str(project.id)
    assert job.source_type == "play_store"


@pytest.mark.asyncio
async def test_create_ingestion_job_unsupported_source(db_session):
    project = ResearchProject(name=f"Unsupported Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()

    with pytest.raises(HTTPException) as exc_info:
        await IngestionService.create_job(
            db=db_session,
            project_id=str(project.id),
            source_type="invalid_platform_xyz",
            config={},
        )
    assert exc_info.value.status_code == 400
    assert "Unsupported source_type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_max_concurrent_jobs_limit(db_session):
    project = ResearchProject(name=f"Concurrency Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    pid = str(project.id)

    # Create 3 active jobs
    for i in range(3):
        job = IngestionJob(project_id=pid, source_type="reddit", status="running", config={})
        db_session.add(job)
    await db_session.commit()

    # 4th job should fail with 409 Conflict
    with pytest.raises(HTTPException) as exc_info:
        await IngestionService.create_job(
            db=db_session,
            project_id=pid,
            source_type="reddit",
            config={},
        )
    assert exc_info.value.status_code == 409
    assert "Maximum allowed concurrent jobs" in exc_info.value.detail


@pytest.mark.asyncio
async def test_job_watchdog_stale_heartbeat(db_session):
    project = ResearchProject(name=f"Watchdog Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()

    stale_time = datetime.now(timezone.utc) - timedelta(seconds=150)
    job = IngestionJob(
        project_id=str(project.id),
        source_type="reddit",
        status="running",
        last_heartbeat_at=stale_time,
        config={},
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    # Retrieval should trigger watchdog failure update
    retrieved = await IngestionService.get_job(db_session, str(project.id), str(job.id))
    assert retrieved.status == "failed"
    assert retrieved.error_details.get("stale_heartbeat") is True


@pytest.mark.asyncio
async def test_job_cancellation(db_session):
    project = ResearchProject(name=f"Cancel Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()

    job = IngestionJob(project_id=str(project.id), source_type="play_store", status="running", config={})
    db_session.add(job)
    await db_session.commit()

    cancelled = await IngestionService.cancel_job(db_session, str(project.id), str(job.id))
    assert cancelled.status == "cancelled"
    assert cancelled.completed_at is not None


@pytest.mark.asyncio
async def test_ingestion_worker_execution():
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Worker Exec Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)

        job = IngestionJob(
            project_id=str(project.id),
            source_type="play_store",
            status="queued",
            config={"mock_mode": True, "limit": 3},
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        job_id = str(job.id)

    # Run worker with test sessionmaker
    await IngestionWorker.run_job(job_id, session_factory=TestAsyncSessionLocal)

    async with TestAsyncSessionLocal() as db:
        finished_job = await IngestionService.get_job(db, str(project.id), job_id)
        assert finished_job.status == "completed"
        assert finished_job.records_found == 3
        assert finished_job.records_stored == 3

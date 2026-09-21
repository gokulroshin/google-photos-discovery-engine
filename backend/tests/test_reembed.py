import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.ingestion_job import IngestionJob
from backend.workers.ingestion_worker import IngestionWorker
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_reembed_job_end_to_end(db_session, researcher_headers):
    # 1. Create project
    proj = ResearchProject(name=f"Reembed Proj {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    # 2. Create source and evidence with stale / null embedding
    src = SourceRecord(
        project_id=str(proj.id),
        source_platform="reddit",
        raw_content="Looking for a photo of nephew wearing red hat in summer 2021.",
        author_handle="user_nephew",
        collection_method="manual_json",
        dedup_hash=f"hash_{uuid.uuid4().hex}",
    )
    db_session.add(src)
    await db_session.commit()
    await db_session.refresh(src)

    ev1 = EvidenceRecord(
        source_record_id=str(src.id),
        is_relevant=True,
        retrieval_scenario="Nephew in red hat",
        evidence_excerpt="nephew wearing red hat",
        embedding=None,  # Needs re-embedding
        embedding_stale=True,
    )
    ev2 = EvidenceRecord(
        source_record_id=str(src.id),
        is_relevant=True,
        retrieval_scenario="Outdated model version record",
        evidence_excerpt="nephew in red hat",
        embedding=[0.1] * 768,
        embedding_model_version="old-embedding-model-001",  # Mismatch
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    # 3. Create re-embedding job via API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.post(
            f"/v1/projects/{proj.id}/jobs",
            json={"source_type": "reembed", "config": {}},
            headers=researcher_headers,
        )

    assert res.status_code == 201
    job_data = res.json()
    job_id = job_data["id"]
    assert job_data["source_type"] == "reembed"

    # 4. Execute worker
    await IngestionWorker.run_job(job_id, session_factory=TestAsyncSessionLocal)

    # 5. Verify job and evidence records
    async with TestAsyncSessionLocal() as session:
        job_stmt = select(IngestionJob).where(IngestionJob.id == job_id)
        job = (await session.execute(job_stmt)).scalar_one()
        assert job.status == "completed"
        assert job.records_found == 2
        assert job.records_stored == 2

        ev_stmt = select(EvidenceRecord).where(EvidenceRecord.source_record_id == str(src.id))
        records = (await session.execute(ev_stmt)).scalars().all()
        for r in records:
            assert r.embedding is not None
            assert len(r.embedding) == 768
            assert r.embedding_stale is False
            assert r.embedding_model_version == "text-embedding-004"

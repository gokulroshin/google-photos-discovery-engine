import pytest
import uuid
from sqlalchemy import select
from unittest.mock import patch
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.model_run import ModelRun
from backend.models.evidence_record import EvidenceRecord
from backend.workers.analysis_worker import AnalysisWorker
from backend.services.analysis_service import AnalysisService
from backend.gemini.client import GeminiUnavailableError
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_analysis_worker_pipeline_execution():
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Analysis Worker Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        # Seed 3 source records: 1 relevant, 1 non-relevant, 1 with specific cue
        r1 = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="I cannot find my photo of a yellow raincoat dog in Chicago from 2021.",
            dedup_hash="hash_a1",
        )
        r2 = SourceRecord(
            project_id=project_id,
            source_platform="play_store",
            raw_content="The app constantly crashes on launch after the latest update.",
            dedup_hash="hash_a2",
        )
        db.add_all([r1, r2])
        await db.commit()

        # Create model run
        model_run = await AnalysisService.create_analysis_run(db, project_id)
        run_id = str(model_run.id)

    # Run Analysis Worker
    await AnalysisWorker.run_analysis_job(run_id, session_factory=TestAsyncSessionLocal)

    # Verify results
    async with TestAsyncSessionLocal() as db:
        finished_run = await AnalysisService.get_model_run(db, project_id, run_id)
        assert finished_run.status == "completed"
        assert finished_run.records_success == 2
        assert finished_run.records_failed == 0

        # Query created evidence records
        evidence_stmt = select(EvidenceRecord).where(EvidenceRecord.model_run_id == run_id)
        evidence_records = list((await db.execute(evidence_stmt)).scalars().all())
        assert len(evidence_records) == 2

        # One should be relevant, one non-relevant
        relevant_rec = next(e for e in evidence_records if e.is_relevant)
        irrelevant_rec = next(e for e in evidence_records if not e.is_relevant)

        assert relevant_rec is not None
        assert relevant_rec.confidence_score >= 0.0
        assert relevant_rec.retrieval_scenario is not None
        assert relevant_rec.embedding is not None

        assert irrelevant_rec is not None
        assert irrelevant_rec.is_relevant is False


@pytest.mark.asyncio
async def test_analysis_idempotency_on_rerun():
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Idempotent Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        r1 = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="Lost picture of sunset on wooden pier in Greece.",
            dedup_hash="hash_idemp_1",
        )
        db.add(r1)
        await db.commit()

        run1 = await AnalysisService.create_analysis_run(db, project_id)
        run1_id = str(run1.id)

    # First run
    await AnalysisWorker.run_analysis_job(run1_id, session_factory=TestAsyncSessionLocal)

    # Second run should find 0 unanalyzed records
    async with TestAsyncSessionLocal() as db:
        run2 = await AnalysisService.create_analysis_run(db, project_id)
        assert run2.records_total == 0
        run2_id = str(run2.id)

    await AnalysisWorker.run_analysis_job(run2_id, session_factory=TestAsyncSessionLocal)

    async with TestAsyncSessionLocal() as db:
        total_ev_stmt = select(EvidenceRecord).join(SourceRecord, EvidenceRecord.source_record_id == SourceRecord.id).where(SourceRecord.project_id == project_id)
        total_ev = list((await db.execute(total_ev_stmt)).scalars().all())
        # Should not create duplicates
        assert len(total_ev) == 1


@pytest.mark.asyncio
async def test_analysis_worker_pauses_on_gemini_outage():
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Outage Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        r1 = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="Looking for bicycle photo in garage.",
            dedup_hash="hash_outage_1",
        )
        db.add(r1)
        await db.commit()

        run = await AnalysisService.create_analysis_run(db, project_id)
        run_id = str(run.id)

    # Simulate Gemini outage
    with patch("backend.gemini.client.GeminiClient.call_gemini", side_effect=GeminiUnavailableError("Gemini 503 Outage")):
        await AnalysisWorker.run_analysis_job(run_id, session_factory=TestAsyncSessionLocal)

    async with TestAsyncSessionLocal() as db:
        paused_run = await AnalysisService.get_model_run(db, project_id, run_id)
        assert paused_run.status == "paused"
        assert paused_run.error_log is not None
        assert "Gemini 503 Outage" in paused_run.error_log.get("error", "")

        # Resume run
        resumed = await AnalysisService.resume_model_run(db, project_id, run_id)
        assert resumed.status == "queued"

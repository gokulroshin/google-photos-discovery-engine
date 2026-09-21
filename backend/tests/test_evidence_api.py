import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.model_run import ModelRun
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_start_analysis_api(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"API Analysis {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        rec = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="Looking for yellow raincoat dog in snow",
            dedup_hash="hash_api_an_1",
        )
        db.add(rec)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Start analysis
        res = await client.post(
            f"/v1/projects/{project_id}/analyze",
            headers=researcher_headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["id"] is not None
        assert data["status"] in ["queued", "running", "completed"]

        # 2nd call while active should return 409 Conflict if still running/queued
        run_id = data["id"]
        # List model runs
        list_res = await client.get(
            f"/v1/projects/{project_id}/model-runs",
            headers=researcher_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 1


@pytest.mark.asyncio
async def test_list_and_get_evidence_records(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Evidence List API {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        source_rec = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            source_url="https://reddit.com/r/googlephotos/ev1",
            raw_content="I searched for my orange tent in Yosemite and search returned zero photos.",
            dedup_hash="hash_ev_api_1",
            author_handle="user_camper",
        )
        db.add(source_rec)
        await db.commit()
        await db.refresh(source_rec)

        model_run = ModelRun(
            project_id=project_id,
            model_name="gemini-1.5-pro",
            prompt_version="1.0.0",
            status="completed",
        )
        db.add(model_run)
        await db.commit()
        await db.refresh(model_run)

        ev1 = EvidenceRecord(
            source_record_id=str(source_rec.id),
            model_run_id=str(model_run.id),
            is_relevant=True,
            relevance_labels=["visual_color_failure", "camping_scene"],
            retrieval_scenario="Finding orange tent in Yosemite",
            memory_cues={"object": "orange tent", "place": "Yosemite"},
            retrieval_outcome="abandoned",
            failure_points=["Color tag mismatch"],
            confidence_score=0.95,
            rationale="Clear user retrieval failure with color memory cue.",
            needs_human_review=False,
            evidence_excerpt="searched for my orange tent in Yosemite",
        )
        db.add(ev1)
        await db.commit()
        await db.refresh(ev1)
        evidence_id = str(ev1.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # List all evidence
        list_res = await client.get(
            f"/v1/projects/{project_id}/evidence",
            headers=researcher_headers,
        )
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] == 1
        assert list_data["total_before_filters"] == 1
        assert list_data["items"][0]["id"] == evidence_id
        assert list_data["items"][0]["retrieval_outcome"] == "abandoned"

        # Filter by outcome
        filter_res = await client.get(
            f"/v1/projects/{project_id}/evidence?outcome=abandoned",
            headers=researcher_headers,
        )
        assert filter_res.status_code == 200
        assert filter_res.json()["total"] == 1

        filter_none = await client.get(
            f"/v1/projects/{project_id}/evidence?outcome=found_immediately",
            headers=researcher_headers,
        )
        assert filter_none.status_code == 200
        assert filter_none.json()["total"] == 0

        # Search filter
        search_res = await client.get(
            f"/v1/projects/{project_id}/evidence?search=orange",
            headers=researcher_headers,
        )
        assert search_res.status_code == 200
        assert search_res.json()["total"] == 1

        # Get single evidence detail
        detail_res = await client.get(
            f"/v1/projects/{project_id}/evidence/{evidence_id}",
            headers=researcher_headers,
        )
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["id"] == evidence_id
        assert detail_data["source_record"] is not None
        assert "orange tent in Yosemite" in detail_data["source_record"]["raw_content"]
        assert detail_data["model_name"] == "gemini-1.5-pro"

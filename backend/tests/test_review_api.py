import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.human_review import HumanReview


@pytest.mark.asyncio
async def test_human_review_queue_and_actions(
    client: AsyncClient,
    db_session: AsyncSession,
    researcher_headers: dict,
):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name=f"Review Test Proj {uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # 1. Create a record that needs human review
    src = SourceRecord(
        id=f"src_rev_{uuid.uuid4().hex[:6]}",
        project_id=project.id,
        source_platform="reddit",
        raw_content="Uncertain query about finding wedding photo with distant relative.",
        dedup_hash=f"hash_rev_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(src)
    await db_session.commit()

    ev = EvidenceRecord(
        id=str(uuid.uuid4()),
        source_record_id=src.id,
        is_relevant=True,
        confidence_score=0.55,
        retrieval_scenario="Uncertain relative query",
        needs_human_review=True,
    )
    db_session.add(ev)
    await db_session.commit()

    # 2. Get human review queue
    res_queue = await client.get(
        f"/v1/projects/{project.id}/evidence",
        params={"needs_review": True},
        headers=researcher_headers,
    )
    assert res_queue.status_code == 200
    queue_data = res_queue.json()
    assert queue_data["total"] >= 1
    found_ids = [item["id"] for item in queue_data["items"]]
    assert ev.id in found_ids

    # 3. Submit human review correction
    res_correct = await client.post(
        f"/v1/projects/{project.id}/evidence/{ev.id}/review",
        headers=researcher_headers,
        json={
            "action": "corrected",
            "corrections": {
                "retrieval_scenario": "Corrected scenario: Cousin wedding retrieval failure",
                "retrieval_outcome": "abandoned",
                "confidence_score": 0.85,
            },
            "reviewer_notes": "Manually verified user experience details.",
        },
    )
    assert res_correct.status_code == 200
    review_resp = res_correct.json()
    assert review_resp["id"] == ev.id
    assert review_resp["retrieval_scenario"] == "Corrected scenario: Cousin wedding retrieval failure"
    assert review_resp["retrieval_outcome"] == "abandoned"
    assert review_resp["confidence_score"] == 0.85
    assert review_resp["needs_human_review"] is False

    # 4. Verify record is updated in DB
    res_updated = await client.get(
        f"/v1/projects/{project.id}/evidence/{ev.id}",
        headers=researcher_headers,
    )
    assert res_updated.status_code == 200
    updated_data = res_updated.json()
    assert updated_data["retrieval_scenario"] == "Corrected scenario: Cousin wedding retrieval failure"
    assert updated_data["retrieval_outcome"] == "abandoned"
    assert updated_data["confidence_score"] == 0.85
    assert updated_data["needs_human_review"] is False

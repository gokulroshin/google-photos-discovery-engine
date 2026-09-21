import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.gemini.client import get_gemini_client


@pytest.mark.asyncio
async def test_semantic_search_with_embeddings(db_session, researcher_headers):
    # 1. Create project
    proj = ResearchProject(
        name=f"Semantic Search Proj {uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    gemini_client = get_gemini_client()

    # 2. Create source records & evidence with embeddings
    src1 = SourceRecord(
        project_id=str(proj.id),
        source_platform="reddit",
        raw_content="Looking for a photo of my dog wearing a yellow raincoat in the snow from winter 2020.",
        author_handle="user_dog_1",
        collection_method="manual_json",
        dedup_hash=f"hash_{uuid.uuid4().hex}",
        is_duplicate=False,
    )
    src2 = SourceRecord(
        project_id=str(proj.id),
        source_platform="play_store",
        raw_content="Searching for receipt from Home Depot but it only shows beach pictures.",
        author_handle="user_receipt_2",
        collection_method="automated_adapter",
        dedup_hash=f"hash_{uuid.uuid4().hex}",
        is_duplicate=False,
    )
    db_session.add_all([src1, src2])
    await db_session.commit()
    await db_session.refresh(src1)
    await db_session.refresh(src2)

    emb1 = await gemini_client.generate_embedding("yellow raincoat dog in snow")
    emb2 = await gemini_client.generate_embedding(src2.raw_content)

    ev1 = EvidenceRecord(
        source_record_id=str(src1.id),
        is_relevant=True,
        retrieval_scenario="Dog yellow raincoat in winter snow",
        evidence_excerpt="dog wearing a yellow raincoat",
        confidence_score=0.95,
        rationale="Clear episodic memory query",
        embedding=emb1,
    )
    ev2 = EvidenceRecord(
        source_record_id=str(src2.id),
        is_relevant=True,
        retrieval_scenario="Home Depot receipt OCR search",
        evidence_excerpt="receipt from Home Depot",
        confidence_score=0.90,
        rationale="OCR receipt failure",
        embedding=emb2,
    )
    db_session.add_all([ev1, ev2])
    await db_session.commit()

    # 3. Test semantic search endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            f"/v1/projects/{proj.id}/evidence/search",
            params={"q": "yellow raincoat dog in snow", "min_similarity": 0.4},
            headers=researcher_headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["query"] == "yellow raincoat dog in snow"
    assert data["total_matches"] >= 1
    assert "similarity_score" in data["items"][0]
    assert data["items"][0]["similarity_score"] >= 0.99


@pytest.mark.asyncio
async def test_semantic_search_low_confidence_fallback(db_session, researcher_headers):
    # Test fallback when threshold is set high but no items reach it
    proj = ResearchProject(name=f"Fallback Proj {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(proj)
    await db_session.commit()

    src = SourceRecord(
        project_id=str(proj.id),
        source_platform="reddit",
        raw_content="Looking for bicycle sunset picture.",
        author_handle="user_bike",
        collection_method="manual_json",
        dedup_hash=f"hash_{uuid.uuid4().hex}",
    )
    db_session.add(src)
    await db_session.commit()

    emb = await get_gemini_client().generate_embedding(src.raw_content)
    ev = EvidenceRecord(
        source_record_id=str(src.id),
        is_relevant=True,
        retrieval_scenario="Sunset bicycle search",
        embedding=emb,
    )
    db_session.add(ev)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            f"/v1/projects/{proj.id}/evidence/search",
            params={"q": "completely unrelated receipt quantum physics", "min_similarity": 0.99},
            headers=researcher_headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["is_low_confidence"] is True
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_semantic_search_keyword_fallback(db_session, researcher_headers):
    # Test keyword search fallback when embeddings are null
    proj = ResearchProject(name=f"KW Proj {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(proj)
    await db_session.commit()

    src = SourceRecord(
        project_id=str(proj.id),
        source_platform="forum",
        raw_content="Searching for my wedding anniversary photo in Greece.",
        author_handle="user_greece",
        collection_method="manual_json",
        dedup_hash=f"hash_{uuid.uuid4().hex}",
    )
    db_session.add(src)
    await db_session.commit()

    ev = EvidenceRecord(
        source_record_id=str(src.id),
        is_relevant=True,
        retrieval_scenario="Wedding in Greece search",
        evidence_excerpt="wedding anniversary photo in Greece",
        embedding=None,  # Null embedding
    )
    db_session.add(ev)
    await db_session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(
            f"/v1/projects/{proj.id}/evidence/search",
            params={"q": "wedding anniversary Greece"},
            headers=researcher_headers,
        )

    assert res.status_code == 200
    data = res.json()
    assert len(data["items"]) >= 1
    assert "Greece" in data["items"][0]["retrieval_scenario"]

import pytest
import uuid
from fastapi import HTTPException
from sqlalchemy import select
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.services.taxonomy_service import TaxonomyService
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_taxonomy_generation_insufficient_evidence(db_session):
    project = ResearchProject(name=f"Taxonomy Empty {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    with pytest.raises(HTTPException) as exc_info:
        await TaxonomyService.generate_taxonomy(db_session, str(project.id))
    assert exc_info.value.status_code == 400
    assert "Insufficient evidence records" in exc_info.value.detail


@pytest.mark.asyncio
async def test_taxonomy_generation_success(db_session):
    project = ResearchProject(name=f"Taxonomy Success {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    project_id = str(project.id)

    # Seed 6 source records and evidence records with unique authors and platforms
    records_to_seed = [
        ("reddit", "user_alpha", "Can't find photo of yellow raincoat dog in Chicago in 2021"),
        ("play_store", "user_beta", "Cannot find receipt from Home Depot 2022 due to OCR failure"),
        ("app_store", "user_gamma", "Lost picture of sunset on wooden pier in Greece with purple sky"),
        ("reddit", "user_delta", "Search by wedding dance failed to return my sister's photo"),
        ("forum", "user_epsilon", "Face recognition grouped distant cousin with random stranger in crowd"),
        ("reddit", "user_alpha", "Repeated search for orange tent in Yosemite gave 0 results"),
    ]

    for i, (platform, author, content) in enumerate(records_to_seed):
        src = SourceRecord(
            project_id=project_id,
            source_platform=platform,
            author_handle=author,
            raw_content=content,
            dedup_hash=f"hash_{uuid.uuid4().hex[:8]}",
        )
        db_session.add(src)
        await db_session.commit()
        await db_session.refresh(src)

        # Unique vector per item
        vec = [0.0] * 768
        vec[i % 768] = 1.0

        ev = EvidenceRecord(
            source_record_id=str(src.id),
            is_relevant=True,
            needs_human_review=False,
            retrieval_scenario=content[:50],
            confidence_score=0.9,
            evidence_excerpt=content[:40],
            embedding=vec,
        )
        db_session.add(ev)
    await db_session.commit()

    # Generate taxonomy v1
    categories = await TaxonomyService.generate_taxonomy(db_session, project_id, k_clusters=3)
    assert len(categories) >= 3
    assert all(c.version == 1 for c in categories)
    assert all(c.evidence_count > 0 for c in categories)
    assert all(c.unique_author_count > 0 for c in categories)
    assert all(isinstance(c.source_diversity, dict) for c in categories)
    assert all(c.confidence_level in ["low", "medium", "high"] for c in categories)

    # Generate taxonomy v2
    cat_v2 = await TaxonomyService.generate_taxonomy(db_session, project_id, k_clusters=3)
    assert all(c.version == 2 for c in cat_v2)

    # List categories
    latest_cats, total, ver = await TaxonomyService.list_categories(db_session, project_id)
    assert total == len(cat_v2)
    assert ver == 2

    # Update category
    target_cat = latest_cats[0]
    updated = await TaxonomyService.update_category(
        db_session,
        project_id,
        str(target_cat.id),
        {"name": "Refined Problem Category Name", "open_questions": ["New Question?"]},
    )
    assert updated.name == "Refined Problem Category Name"
    assert updated.open_questions == ["New Question?"]

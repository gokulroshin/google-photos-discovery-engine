import pytest
import uuid
import hashlib
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.opportunity_area import OpportunityArea
from backend.models.human_review import HumanReview


@pytest.mark.asyncio
async def test_full_model_lifecycle(db_session):
    uid = uuid.uuid4().hex[:8]
    # 1. Create Project
    project = ResearchProject(
        name=f"Model Lifecycle Test Project {uid}",
        description="Testing relationships",
        research_questions=["How do memory cues fail?"],
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # 2. Create SourceRecord
    content = f"I searched for photos of my dog at the beach last summer {uid}."
    dedup_hash = hashlib.sha256(content.encode()).hexdigest()
    source_rec = SourceRecord(
        project_id=project.id,
        source_platform="reddit",
        raw_content=content,
        author_handle="user_a1b2c",
        dedup_hash=dedup_hash,
        metadata_json={"subreddit": "googlephotos", "upvotes": 12},
    )
    db_session.add(source_rec)
    await db_session.commit()
    await db_session.refresh(source_rec)

    # 3. Create EvidenceRecord
    evidence = EvidenceRecord(
        source_record_id=source_rec.id,
        is_relevant=True,
        relevance_labels=["animal", "location", "seasonal_time"],
        retrieval_scenario="Dog at beach during summer",
        memory_cues={"object": "dog", "place": "beach", "time": "last summer"},
        confidence_score=0.92,
        rationale="User explicitly recounts trying to search by episodic visual cues.",
        embedding=[0.05] * 768,
    )
    db_session.add(evidence)
    await db_session.commit()
    await db_session.refresh(evidence)

    # 4. Create HumanReview
    review = HumanReview(
        evidence_record_id=evidence.id,
        reviewer_id="usr_reviewer_1",
        action="approved",
        reviewer_notes="High quality episodic retrieval failure.",
    )
    db_session.add(review)

    # 5. Create TaxonomyCategory & OpportunityArea
    category = TaxonomyCategory(
        project_id=project.id,
        name=f"Seasonal & Episodic Activity Failure {uid}",
        definition="Failures where temporal reference is relative rather than timestamped.",
        failure_mechanism="Lack of relative temporal grounding in search index.",
        evidence_count=1,
        representative_excerpts=[evidence.evidence_excerpt or "beach last summer"],
    )
    db_session.add(category)
    await db_session.commit()
    await db_session.refresh(category)

    opp = OpportunityArea(
        project_id=project.id,
        taxonomy_category_id=category.id,
        name=f"Relative Temporal Query Parser {uid}",
        description="Enable natural language searches like 'last summer'.",
        evidence_frequency=1,
        user_impact_score=8.5,
        strategic_relevance=9.0,
    )
    db_session.add(opp)
    await db_session.commit()
    await db_session.refresh(opp)

    assert project.id is not None
    assert source_rec.id is not None
    assert evidence.id is not None
    assert category.id is not None
    assert opp.id is not None
    assert len(evidence.embedding) == 768

import pytest
import uuid
from fastapi import HTTPException
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.opportunity_area import OpportunityArea
from backend.services.opportunity_service import OpportunityService
from backend.services.taxonomy_service import TaxonomyService


@pytest.mark.asyncio
async def test_opportunity_generation_and_scoring(db_session):
    project = ResearchProject(name=f"Opportunity Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    project_id = str(project.id)

    # Seed 3 categories
    cat1 = TaxonomyCategory(
        project_id=project_id,
        version=1,
        name="Incomplete Temporal Memory",
        definition="Users forget calendar dates for events",
        evidence_count=12,
        unique_author_count=8,
        source_diversity={"reddit": 7, "play_store": 5},
        confidence_level="high",
        failure_mechanism="Timeline scrolling failure",
    )
    cat2 = TaxonomyCategory(
        project_id=project_id,
        version=1,
        name="Speculative Future Failure",
        definition="No evidence gathered yet",
        evidence_count=0,
        unique_author_count=0,
        source_diversity={},
        confidence_level="low",
        failure_mechanism="Unknown",
    )
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    # Generate opportunities
    opportunities = await OpportunityService.generate_opportunities(db_session, project_id)
    assert len(opportunities) == 2

    # Verify 9 dimensions on generated areas
    opp1 = next(o for o in opportunities if o.taxonomy_category_id == str(cat1.id))
    assert opp1.evidence_frequency == 12
    assert opp1.user_impact_score >= 0.0
    assert 0.0 <= opp1.abandonment_rate <= 1.0
    assert opp1.strategic_relevance >= 0.0
    assert opp1.problem_clarity >= 0.0
    assert opp1.validation_effort in ["low", "medium", "high"]
    assert opp1.scoring_methodology is not None
    assert opp1.status in ["draft", "validated"]

    opp2 = next(o for o in opportunities if o.taxonomy_category_id == str(cat2.id))
    assert opp2.evidence_frequency == 0
    assert opp2.status == "speculative"


@pytest.mark.asyncio
async def test_opportunity_manual_override_validation(db_session):
    project = ResearchProject(name=f"Override Test {uuid.uuid4().hex[:6]}", status="active")
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    project_id = str(project.id)

    opp = OpportunityArea(
        project_id=project_id,
        name="Opportunity: Vague Visual Cues",
        description="Search by color and light",
        user_impact_score=5.0,
        strategic_relevance=6.0,
        status="draft",
    )
    db_session.add(opp)
    await db_session.commit()
    await db_session.refresh(opp)
    opp_id = str(opp.id)

    # Attempt score update WITHOUT analyst_notes -> Should fail with 422
    with pytest.raises(HTTPException) as exc_info:
        await OpportunityService.update_opportunity(
            db_session,
            project_id,
            opp_id,
            {"user_impact_score": 9.5},  # Changing score without notes
        )
    assert exc_info.value.status_code == 422
    assert "analyst_notes" in exc_info.value.detail

    # Updating WITH analyst_notes -> Should succeed
    updated = await OpportunityService.update_opportunity(
        db_session,
        project_id,
        opp_id,
        {"user_impact_score": 9.5, "analyst_notes": "Upgraded score based on executive review."},
    )
    assert updated.user_impact_score == 9.5
    assert updated.analyst_notes == "Upgraded score based on executive review."

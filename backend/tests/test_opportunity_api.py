import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.taxonomy_category import TaxonomyCategory
from backend.models.opportunity_area import OpportunityArea
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_opportunity_api_generate_and_list(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Opp API Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        # Seed category
        cat = TaxonomyCategory(
            project_id=project_id,
            version=1,
            name="Missing Metadata Category",
            definition="Users don't know the exact year",
            evidence_count=8,
            unique_author_count=5,
            source_diversity={"reddit": 8},
            failure_mechanism="Tag indexing failure",
        )
        db.add(cat)
        await db.commit()
        await db.refresh(cat)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate opportunities
        gen_res = await client.post(
            f"/v1/projects/{project_id}/opportunities",
            headers=researcher_headers,
        )
        assert gen_res.status_code == 201
        gen_data = gen_res.json()
        assert gen_data["total"] == 1
        opp_id = gen_data["items"][0]["id"]
        assert gen_data["items"][0]["evidence_frequency"] == 8

        # List opportunities
        list_res = await client.get(
            f"/v1/projects/{project_id}/opportunities",
            headers=researcher_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 1

        # Get single opportunity
        get_res = await client.get(
            f"/v1/projects/{project_id}/opportunities/{opp_id}",
            headers=researcher_headers,
        )
        assert get_res.status_code == 200
        assert get_res.json()["id"] == opp_id

        # Update without analyst_notes (score changed) -> 422
        bad_patch = await client.patch(
            f"/v1/projects/{project_id}/opportunities/{opp_id}",
            json={"user_impact_score": 9.9},
            headers=researcher_headers,
        )
        assert bad_patch.status_code == 422

        # Update with analyst_notes -> 200
        good_patch = await client.patch(
            f"/v1/projects/{project_id}/opportunities/{opp_id}",
            json={"user_impact_score": 9.9, "analyst_notes": "Validated with leadership."},
            headers=researcher_headers,
        )
        assert good_patch.status_code == 200
        assert good_patch.json()["user_impact_score"] == 9.9
        assert good_patch.json()["analyst_notes"] == "Validated with leadership."

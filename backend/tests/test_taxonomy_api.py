import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_taxonomy_api_generate_and_list(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Taxonomy API Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        # Seed 4 evidence records
        for i in range(4):
            src = SourceRecord(
                project_id=project_id,
                source_platform="reddit",
                raw_content=f"Cannot find photo {i+1} yellow dog",
                dedup_hash=f"hash_tax_api_{i}",
            )
            db.add(src)
            await db.commit()
            await db.refresh(src)

            ev = EvidenceRecord(
                source_record_id=str(src.id),
                is_relevant=True,
                needs_human_review=False,
                confidence_score=0.9,
                retrieval_scenario="Lost dog picture",
            )
            db.add(ev)
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Generate taxonomy
        gen_res = await client.post(
            f"/v1/projects/{project_id}/taxonomy/generate?k_clusters=3",
            headers=researcher_headers,
        )
        assert gen_res.status_code == 200
        gen_data = gen_res.json()
        assert gen_data["total"] >= 3
        assert gen_data["version"] == 1
        cat_id = gen_data["items"][0]["id"]

        # List taxonomy categories
        list_res = await client.get(
            f"/v1/projects/{project_id}/taxonomy",
            headers=researcher_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["total"] >= 3

        # Get single category
        get_res = await client.get(
            f"/v1/projects/{project_id}/taxonomy/{cat_id}",
            headers=researcher_headers,
        )
        assert get_res.status_code == 200
        assert get_res.json()["id"] == cat_id

        # Patch category
        patch_res = await client.patch(
            f"/v1/projects/{project_id}/taxonomy/{cat_id}",
            json={"name": "Updated Category Title"},
            headers=researcher_headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["name"] == "Updated Category Title"

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.tests.conftest import TestAsyncSessionLocal


@pytest.mark.asyncio
async def test_manual_csv_import_api(researcher_headers):
    # 1. Create project
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"API Import Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

    csv_data = """raw_content,source_url,source_date,source_platform,author_handle
"Cannot find my cat in the laundry basket",https://example.com/cat1,2024-02-01,reddit,cat_lover
"Search by color orange returned nothing",https://example.com/cat2,2024-02-02,play_store,reviewer_2
"""
    files = {"file": ("dataset.csv", csv_data.encode("utf-8"), "text/csv")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/v1/projects/{project_id}/import",
            files=files,
            headers=researcher_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["records_accepted"] == 2
        assert data["records_skipped_duplicate"] == 0
        assert data["records_failed"] == 0


@pytest.mark.asyncio
async def test_manual_csv_import_missing_columns_validation(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Bad CSV Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

    # Missing source_url, source_date
    bad_csv = """raw_content,source_platform
"Search failed again",forum
"""
    files = {"file": ("bad.csv", bad_csv.encode("utf-8"), "text/csv")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/v1/projects/{project_id}/import",
            files=files,
            headers=researcher_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "validation_errors" in data["detail"]


@pytest.mark.asyncio
async def test_manual_import_deduplication(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Dedup API Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

    csv_data = """raw_content,source_url,source_date,source_platform
"I tried searching for my tax document from 2020 and got zero matches.",https://example.com/tax1,2024-03-01,reddit
"""
    files1 = {"file": ("test.csv", csv_data.encode("utf-8"), "text/csv")}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First import
        res1 = await client.post(
            f"/v1/projects/{project_id}/import",
            files=files1,
            headers=researcher_headers,
        )
        assert res1.status_code == 200
        assert res1.json()["records_accepted"] == 1

        # Second import with same content, different URL
        csv_data2 = """raw_content,source_url,source_date,source_platform
"  I tried searching for my tax document from 2020 and got zero matches.  ",https://example.com/tax2,2024-03-01,reddit
"""
        files2 = {"file": ("test.csv", csv_data2.encode("utf-8"), "text/csv")}
        res2 = await client.post(
            f"/v1/projects/{project_id}/import",
            files=files2,
            headers=researcher_headers,
        )
        assert res2.status_code == 200
        assert res2.json()["records_accepted"] == 0
        assert res2.json()["records_skipped_duplicate"] == 1


@pytest.mark.asyncio
async def test_list_records_and_filters(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Filter List Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        # Seed records
        r1 = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="Looking for bicycle in garage photo",
            dedup_hash="hash_bicycle_1",
            author_handle="user_a",
            language="en",
        )
        r2 = SourceRecord(
            project_id=project_id,
            source_platform="play_store",
            raw_content="No puedo encontrar mis fotos de Madrid",
            dedup_hash="hash_madrid_2",
            author_handle="user_b",
            language="es",
        )
        db.add_all([r1, r2])
        await db.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Unfiltered
        res = await client.get(f"/v1/projects/{project_id}/records", headers=researcher_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["total"] == 2
        assert data["total_before_filters"] == 2

        # Filter by platform
        res_platform = await client.get(
            f"/v1/projects/{project_id}/records?platform=reddit",
            headers=researcher_headers,
        )
        assert res_platform.status_code == 200
        assert res_platform.json()["total"] == 1
        assert res_platform.json()["items"][0]["source_platform"] == "reddit"
        assert res_platform.json()["total_before_filters"] == 2

        # Filter by language
        res_lang = await client.get(
            f"/v1/projects/{project_id}/records?language=es",
            headers=researcher_headers,
        )
        assert res_lang.status_code == 200
        assert res_lang.json()["total"] == 1
        assert res_lang.json()["items"][0]["language"] == "es"

        # Search query
        res_search = await client.get(
            f"/v1/projects/{project_id}/records?search=bicycle",
            headers=researcher_headers,
        )
        assert res_search.status_code == 200
        assert res_search.json()["total"] == 1
        assert "bicycle" in res_search.json()["items"][0]["raw_content"]


@pytest.mark.asyncio
async def test_get_and_delete_source_record(researcher_headers):
    async with TestAsyncSessionLocal() as db:
        project = ResearchProject(name=f"Get Delete Test {uuid.uuid4().hex[:6]}", status="active")
        db.add(project)
        await db.commit()
        await db.refresh(project)
        project_id = str(project.id)

        rec = SourceRecord(
            project_id=project_id,
            source_platform="reddit",
            raw_content="To be deleted record",
            dedup_hash="hash_delete_me",
            author_handle="user_c",
        )
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
        record_id = str(rec.id)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Get record
        get_res = await client.get(
            f"/v1/projects/{project_id}/records/{record_id}",
            headers=researcher_headers,
        )
        assert get_res.status_code == 200
        assert get_res.json()["id"] == record_id

        # Delete record
        del_res = await client.delete(
            f"/v1/projects/{project_id}/records/{record_id}",
            headers=researcher_headers,
        )
        assert del_res.status_code == 204

        # Verify not in active list
        list_res = await client.get(
            f"/v1/projects/{project_id}/records",
            headers=researcher_headers,
        )
        assert list_res.status_code == 200
        assert list_res.json()["total"] == 0

import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.models.ingestion_job import IngestionJob


@pytest.mark.asyncio
async def test_create_and_get_project(admin_headers):
    uid = uuid.uuid4().hex[:8]
    project_payload = {
        "name": f"Test Photo Discovery Project {uid}",
        "description": "Evaluating episodic cues",
        "research_questions": ["What cues fail most often?"],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create
        res = await ac.post("/v1/projects", json=project_payload, headers=admin_headers)
        assert res.status_code == 201
        created = res.json()
        assert created["name"] == project_payload["name"]
        project_id = created["id"]

        # Get
        res_get = await ac.get(f"/v1/projects/{project_id}", headers=admin_headers)
        assert res_get.status_code == 200
        detail = res_get.json()
        assert detail["id"] == project_id
        assert detail["record_count"] == 0
        assert detail["active_jobs_count"] == 0


@pytest.mark.asyncio
async def test_duplicate_project_name_rejected(admin_headers):
    uid = uuid.uuid4().hex[:8]
    payload = {
        "name": f"Unique Project Name {uid}",
        "description": "Description",
        "research_questions": [],
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # First creation
        res1 = await ac.post("/v1/projects", json=payload, headers=admin_headers)
        assert res1.status_code == 201

        # Duplicate creation
        res2 = await ac.post("/v1/projects", json=payload, headers=admin_headers)
        assert res2.status_code == 409
        assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_filter_projects(admin_headers):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/v1/projects?page=1&page_size=10", headers=admin_headers)
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert data["page"] == 1


@pytest.mark.asyncio
async def test_update_project(admin_headers):
    uid = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create
        create_res = await ac.post(
            "/v1/projects",
            json={"name": f"Project For Update {uid}", "description": "Original"},
            headers=admin_headers,
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        # Update
        update_res = await ac.patch(
            f"/v1/projects/{project_id}",
            json={"description": "Updated Description", "status": "draft"},
            headers=admin_headers,
        )
        assert update_res.status_code == 200
        updated = update_res.json()
        assert updated["description"] == "Updated Description"
        assert updated["status"] == "draft"


@pytest.mark.asyncio
async def test_delete_project_admin_only(admin_headers, researcher_headers):
    uid = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create project
        create_res = await ac.post(
            "/v1/projects",
            json={"name": f"Project To Delete {uid}", "description": "Temp"},
            headers=admin_headers,
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

        # Researcher tries to delete (should be forbidden: 403)
        res_forbidden = await ac.delete(f"/v1/projects/{project_id}", headers=researcher_headers)
        assert res_forbidden.status_code == 403

        # Admin deletes
        res_delete = await ac.delete(f"/v1/projects/{project_id}", headers=admin_headers)
        assert res_delete.status_code == 204

        # Verify not found after delete
        res_get = await ac.get(f"/v1/projects/{project_id}", headers=admin_headers)
        assert res_get.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_blocked_if_active_jobs(admin_headers, db_session):
    uid = uuid.uuid4().hex[:8]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create project
        create_res = await ac.post(
            "/v1/projects",
            json={"name": f"Project With Active Jobs {uid}", "description": "Temp"},
            headers=admin_headers,
        )
        assert create_res.status_code == 201
        project_id = create_res.json()["id"]

    # Insert an active job directly into the test database
    job = IngestionJob(
        project_id=project_id,
        source_type="manual_csv",
        status="running",
        config={},
    )
    db_session.add(job)
    await db_session.commit()

    # Admin attempts delete -> Should return 409 Conflict
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_del = await ac.delete(f"/v1/projects/{project_id}", headers=admin_headers)
        assert res_del.status_code == 409
        assert "Cannot delete project while" in res_del.json()["detail"]

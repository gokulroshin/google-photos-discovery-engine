import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory


@pytest.mark.asyncio
async def test_report_api_lifecycle(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    # Create project
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="API Report Test Project",
        description="Testing report generation endpoints",
        research_questions=["How to summarize findings?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Seed 12 evidence records
    for i in range(12):
        src = SourceRecord(
            id=f"src_rpt_api_{i}",
            project_id=project.id,
            source_platform="reddit",
            raw_content=f"Cannot find wedding photo #{i}",
            author_handle=f"user_rpt_{i}",
            dedup_hash=f"hash_rpt_api_{i}",
        )
        db_session.add(src)
        await db_session.commit()

        ev = EvidenceRecord(
            id=str(uuid.uuid4()),
            source_record_id=src.id,
            is_relevant=True,
            evidence_excerpt=f"Cannot find wedding photo #{i}",
            confidence_score=0.88,
        )
        db_session.add(ev)
    await db_session.commit()

    # Seed category
    cat = TaxonomyCategory(
        id=str(uuid.uuid4()),
        project_id=project.id,
        version=1,
        name="Wedding Memory Failures",
        definition="Inability to locate specific wedding and milestone photos",
        user_segment="General Users",
        failure_mechanism="Missing temporal clustering",
        evidence_count=12,
        unique_author_count=12,
        confidence_level="high",
        representative_excerpts=["Cannot find wedding photo #0"],
    )
    db_session.add(cat)
    await db_session.commit()

    # 1. Trigger report generation
    res = await client.post(
        f"/v1/projects/{project.id}/reports/generate",
        headers=auth_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project.id
    assert data["evidence_count"] == 12
    assert "markdown" in data
    assert "Wedding Memory Failures" in data["markdown"]
    report_id = data["id"]

    # 2. List reports
    list_res = await client.get(
        f"/v1/projects/{project.id}/reports",
        headers=auth_headers,
    )
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert len(list_data) >= 1
    assert list_data[0]["id"] == report_id

    # 3. Get latest report (JSON)
    latest_res = await client.get(
        f"/v1/projects/{project.id}/reports/latest",
        headers=auth_headers,
    )
    assert latest_res.status_code == 200
    assert latest_res.json()["id"] == report_id

    # 4. Get report as Markdown via query param
    md_res = await client.get(
        f"/v1/projects/{project.id}/reports/{report_id}?format=markdown",
        headers=auth_headers,
    )
    assert md_res.status_code == 200
    assert "text/markdown" in md_res.headers.get("content-type", "")
    assert "# Research Discovery Report" in md_res.text

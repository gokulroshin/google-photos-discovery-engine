import pytest
import uuid
import csv
import io
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory


@pytest.mark.asyncio
async def test_evidence_export_csv_and_json(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="Export Test Project",
        description="Testing CSV & JSON exports",
        research_questions=["How are exports structured?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # Seed source and evidence records with tricky characters: commas, quotes, newlines
    src = SourceRecord(
        id="src_export_01",
        project_id=project.id,
        source_platform="reddit",
        source_url="https://reddit.com/r/googlephotos/123",
        raw_content="I searched for \"blue car, red bicycle\"\nand it returned nothing!",
        author_handle="user_99a8b",
        dedup_hash="hash_exp_01",
    )
    db_session.add(src)
    await db_session.commit()

    ev = EvidenceRecord(
        id=str(uuid.uuid4()),
        source_record_id=src.id,
        is_relevant=True,
        retrieval_scenario="Multi-item search with punctuation",
        memory_cues={"object": "blue car, red bicycle"},
        missing_information="Timestamp",
        search_behavior="Natural language query",
        retrieval_outcome="never_found",
        failure_points=["comma_tokenization_error", "multiline_parse"],
        user_segment="Casual User",
        evidence_excerpt="searched for \"blue car, red bicycle\"\nand it returned nothing",
        confidence_score=0.91,
        rationale="Tested with complex text and quotes.",
        needs_human_review=False,
    )
    db_session.add(ev)
    await db_session.commit()

    # 1. Test CSV export
    csv_res = await client.get(
        f"/v1/projects/{project.id}/export/evidence?format=csv",
        headers=auth_headers,
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert f'filename="evidence_{project.id}.csv"' in csv_res.headers.get("content-disposition", "")
    
    # Check UTF-8 BOM
    raw_bytes = csv_res.content
    assert raw_bytes.startswith(b"\xef\xbb\xbf") or csv_res.text.startswith("\ufeff")

    # Parse with standard Python csv module to ensure valid formatting
    f = io.StringIO(csv_res.text.lstrip("\ufeff"))
    reader = csv.reader(f)
    rows = list(reader)
    assert len(rows) == 2  # Header + 1 record
    header = rows[0]
    data_row = rows[1]
    assert "source_record_id" in header
    assert "author_handle" in header
    assert "user_99a8b" in data_row
    assert data_row[header.index("source_record_id")] == "src_export_01"
    # Ensure quotes and newlines survived parsing intact
    assert "blue car, red bicycle" in data_row[header.index("evidence_excerpt")]

    # 2. Test JSON export
    json_res = await client.get(
        f"/v1/projects/{project.id}/export/evidence?format=json",
        headers=auth_headers,
    )
    assert json_res.status_code == 200
    assert f'filename="evidence_{project.id}.json"' in json_res.headers.get("content-disposition", "")
    json_data = json_res.json()
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]["source_record_id"] == "src_export_01"
    assert json_data[0]["author_handle"] == "user_99a8b"
    assert json_data[0]["retrieval_outcome"] == "never_found"


@pytest.mark.asyncio
async def test_taxonomy_export_csv_and_json(client: AsyncClient, db_session: AsyncSession, auth_headers: dict):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name="Taxonomy Export Project",
        description="Testing taxonomy export",
        research_questions=["What categories exist?"],
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    cat = TaxonomyCategory(
        id=str(uuid.uuid4()),
        project_id=project.id,
        version=1,
        name="Complex Episodic Conjunction, Failure",
        definition="User remembers \"multiple objects, colors\" at once.",
        user_segment="Power Users",
        failure_mechanism="Semantic disjunction",
        evidence_count=24,
        unique_author_count=18,
        confidence_level="high",
        product_implications="Multi-modal ranking boost",
        representative_excerpts=["Red shoes, white socks", "Yellow car at sunset"],
        open_questions=["What is the abandon rate?"],
    )
    db_session.add(cat)
    await db_session.commit()

    # 1. Test CSV export
    csv_res = await client.get(
        f"/v1/projects/{project.id}/export/taxonomy?format=csv",
        headers=auth_headers,
    )
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert f'filename="taxonomy_{project.id}.csv"' in csv_res.headers.get("content-disposition", "")

    f = io.StringIO(csv_res.text.lstrip("\ufeff"))
    reader = csv.reader(f)
    rows = list(reader)
    assert len(rows) == 2
    header = rows[0]
    data_row = rows[1]
    assert "name" in header
    assert "definition" in header
    assert data_row[header.index("name")] == "Complex Episodic Conjunction, Failure"
    assert data_row[header.index("evidence_count")] == "24"

    # 2. Test JSON export
    json_res = await client.get(
        f"/v1/projects/{project.id}/export/taxonomy?format=json",
        headers=auth_headers,
    )
    assert json_res.status_code == 200
    json_data = json_res.json()
    assert isinstance(json_data, list)
    assert len(json_data) == 1
    assert json_data[0]["name"] == "Complex Episodic Conjunction, Failure"
    assert json_data[0]["evidence_count"] == 24

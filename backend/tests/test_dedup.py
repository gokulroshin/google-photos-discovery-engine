import pytest
import hashlib
from backend.adapters.base import SourceAdapter, RawRecord
from backend.services.preprocessing_service import PreprocessingService


class DummyAdapter(SourceAdapter):
    platform_name = "dummy"
    async def fetch(self, config):
        return []
    def normalize(self, raw):
        return PreprocessingService.preprocess_raw_record(raw)


def test_dedup_hash_whitespace_normalization():
    adapter = DummyAdapter()
    
    text1 = "I searched for my yellow dog raincoat in Chicago."
    text2 = "  I   searched for  my   yellow dog raincoat in Chicago. \n\n"
    text3 = "i searched for my yellow dog raincoat in chicago."

    hash1 = adapter.compute_dedup_hash(text1)
    hash2 = adapter.compute_dedup_hash(text2)
    hash3 = adapter.compute_dedup_hash(text3)

    assert hash1 == hash2, "Whitespace variance should yield identical dedup hash"
    assert hash1 == hash3, "Case differences should yield identical dedup hash"


def test_dedup_hash_distinct_content():
    adapter = DummyAdapter()
    
    text1 = "Cannot find my dog photo in Chicago"
    text2 = "Cannot find my cat photo in Chicago"

    hash1 = adapter.compute_dedup_hash(text1)
    hash2 = adapter.compute_dedup_hash(text2)

    assert hash1 != hash2, "Distinct content must produce distinct hashes"


@pytest.mark.asyncio
async def test_cross_project_dedup_scoping(db_session, researcher_headers):
    """Verifies that identical content in two distinct research projects is allowed and scoped per-project."""
    from backend.models.project import ResearchProject
    from backend.models.source_record import SourceRecord
    import uuid

    # Create Project 1 and Project 2
    p1 = ResearchProject(id=str(uuid.uuid4()), name=f"Proj 1 {uuid.uuid4().hex[:4]}", status="active")
    p2 = ResearchProject(id=str(uuid.uuid4()), name=f"Proj 2 {uuid.uuid4().hex[:4]}", status="active")
    db_session.add_all([p1, p2])
    await db_session.commit()

    content = "Identical feedback across multiple separate discovery projects."
    dedup_hash = hashlib.sha256(content.lower().encode("utf-8")).hexdigest()

    rec1 = SourceRecord(
        id=f"src_{uuid.uuid4().hex[:6]}",
        project_id=p1.id,
        source_platform="reddit",
        raw_content=content,
        dedup_hash=dedup_hash,
    )
    rec2 = SourceRecord(
        id=f"src_{uuid.uuid4().hex[:6]}",
        project_id=p2.id,
        source_platform="reddit",
        raw_content=content,
        dedup_hash=dedup_hash,
    )

    db_session.add_all([rec1, rec2])
    await db_session.commit()

    assert rec1.id != rec2.id
    assert rec1.project_id == p1.id
    assert rec2.project_id == p2.id

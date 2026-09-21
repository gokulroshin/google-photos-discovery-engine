import pytest
import uuid
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.models.project import ResearchProject
from backend.models.source_record import SourceRecord
from backend.models.evidence_record import EvidenceRecord
from backend.models.taxonomy_category import TaxonomyCategory
from backend.services.pii_service import PIIService
from backend.auth.rate_limiter import login_rate_limiter
from backend.auth.jwt import decode_token


@pytest.mark.asyncio
async def test_role_enforcement_admin_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
    researcher_headers: dict,
    admin_headers: dict,
):
    # Setup test project
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name=f"Sec Test Project {uuid.uuid4().hex[:6]}",
        description="Testing role enforcement",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    # 1. Project Delete - Researcher should get 403 Forbidden
    res_delete = await client.delete(
        f"/v1/projects/{project.id}",
        headers=researcher_headers,
    )
    assert res_delete.status_code == 403
    assert "Access denied" in res_delete.json()["detail"]

    # 2. Taxonomy Merge - Researcher should get 403 Forbidden
    cat1 = TaxonomyCategory(
        id=str(uuid.uuid4()),
        project_id=project.id,
        version=1,
        name="Cat A",
        definition="Def A",
        failure_mechanism="Fail A",
        evidence_count=5,
        unique_author_count=5,
        confidence_level="medium",
    )
    cat2 = TaxonomyCategory(
        id=str(uuid.uuid4()),
        project_id=project.id,
        version=1,
        name="Cat B",
        definition="Def B",
        failure_mechanism="Fail B",
        evidence_count=5,
        unique_author_count=5,
        confidence_level="medium",
    )
    db_session.add_all([cat1, cat2])
    await db_session.commit()

    res_merge = await client.post(
        f"/v1/projects/{project.id}/taxonomy/merge",
        headers=researcher_headers,
        json={"source_category_ids": [cat1.id, cat2.id], "target_category_name": "Merged Cat"},
    )
    assert res_merge.status_code == 403

    # 3. Admin successfully merges taxonomy
    admin_merge = await client.post(
        f"/v1/projects/{project.id}/taxonomy/merge",
        headers=admin_headers,
        json={"source_category_ids": [cat1.id, cat2.id], "target_category_name": "Merged Cat"},
    )
    assert admin_merge.status_code == 200
    assert admin_merge.json()["name"] == "Merged Cat"

    # 4. Bulk Delete Evidence - Researcher should get 403 Forbidden
    src = SourceRecord(
        id=f"src_sec_{uuid.uuid4().hex[:6]}",
        project_id=project.id,
        source_platform="reddit",
        raw_content="Evidence content",
        author_handle="user_sec_1",
        dedup_hash=f"hash_sec_{uuid.uuid4().hex[:6]}",
    )
    db_session.add(src)
    await db_session.commit()

    ev = EvidenceRecord(
        id=str(uuid.uuid4()),
        source_record_id=src.id,
        is_relevant=True,
        confidence_score=0.85,
    )
    db_session.add(ev)
    await db_session.commit()

    res_bulk_delete = await client.request(
        "DELETE",
        f"/v1/projects/{project.id}/evidence/bulk",
        headers=researcher_headers,
        json={"evidence_record_ids": [ev.id]},
    )
    assert res_bulk_delete.status_code == 403

    # 5. Admin successfully performs bulk delete
    admin_bulk_delete = await client.request(
        "DELETE",
        f"/v1/projects/{project.id}/evidence/bulk",
        headers=admin_headers,
        json={"evidence_record_ids": [ev.id]},
    )
    assert admin_bulk_delete.status_code == 200
    assert admin_bulk_delete.json()["deleted_count"] == 1


@pytest.mark.asyncio
async def test_login_rate_limiting(client: AsyncClient):
    # Reset state for test client IP
    login_rate_limiter.reset_for_ip("127.0.0.1")

    # Make 10 attempts
    for i in range(10):
        res = await client.post(
            "/v1/auth/login",
            json={"email": "researcher@google-photos.internal", "password": "Password123!"},
        )
        assert res.status_code == 200

    # 11th attempt should trigger 429 Too Many Requests
    blocked_res = await client.post(
        "/v1/auth/login",
        json={"email": "researcher@google-photos.internal", "password": "Password123!"},
    )
    assert blocked_res.status_code == 429
    assert "Too many login attempts" in blocked_res.json()["detail"]

    # Clean up
    login_rate_limiter.reset_for_ip("127.0.0.1")


@pytest.mark.asyncio
async def test_jwt_token_expiry_and_claims(client: AsyncClient):
    login_rate_limiter.reset_for_ip("127.0.0.1")

    res = await client.post(
        "/v1/auth/login",
        json={"email": "admin@google-photos.internal", "password": "AdminPassword123!", "role": "admin"},
    )
    assert res.status_code == 200
    data = res.json()
    token = data["access_token"]
    assert data["expires_in"] == 480 * 60  # 8 hours in seconds

    claims = decode_token(token)
    assert claims["role"] == "admin"
    assert claims["email"] == "admin@google-photos.internal"
    assert "sub" in claims
    assert "exp" in claims
    assert "iat" in claims


def test_pii_detection_and_redaction():
    text_with_pii = (
        "Contact me at john.doe@example.com or call 415-555-2671. "
        "My SSN is 123-45-6789."
    )

    entities = PIIService.detect_pii(text_with_pii)
    types_found = {e["type"] for e in entities}
    assert "email" in types_found
    assert "phone" in types_found
    assert "ssn" in types_found

    redacted = PIIService.redact_pii(text_with_pii)
    assert "john.doe@example.com" not in redacted
    assert "415-555-2671" not in redacted
    assert "123-45-6789" not in redacted
    assert "[REDACTED]" in redacted


def test_config_production_security_validation():
    # 1. Mock mode in production must fail
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            MOCK_DATA_MODE=True,
            JWT_SECRET_KEY="a" * 32,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
            ALLOWED_ORIGINS=["https://app.google.com"],
        )
    assert "MOCK_DATA_MODE cannot be enabled" in str(exc.value)

    # 2. Wildcard CORS in production must fail
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            MOCK_DATA_MODE=False,
            ALLOWED_ORIGINS="*",
            JWT_SECRET_KEY="a" * 32,
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
            GEMINI_API_KEY="test_key",
        )
    assert "ALLOWED_ORIGINS cannot contain wildcard '*'" in str(exc.value)

    # 3. SQLite in production must fail
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            MOCK_DATA_MODE=False,
            ALLOWED_ORIGINS=["https://app.google.com"],
            JWT_SECRET_KEY="a" * 32,
            DATABASE_URL="sqlite+aiosqlite:///./test.db",
            GEMINI_API_KEY="test_key",
        )
    assert "DATABASE_URL must be PostgreSQL with pgvector" in str(exc.value)

    # 4. Short / insecure JWT secret in production must fail
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            MOCK_DATA_MODE=False,
            ALLOWED_ORIGINS=["https://app.google.com"],
            JWT_SECRET_KEY="dev-insecure-short",
            DATABASE_URL="postgresql+asyncpg://user:pass@localhost/db",
            GEMINI_API_KEY="test_key",
        )
    assert "JWT_SECRET_KEY must be a secure random secret" in str(exc.value)


@pytest.mark.asyncio
async def test_security_headers_middleware(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains"
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"


def test_logger_sensitive_data_filtering():
    from backend.logger import filter_sensitive_data

    event = {
        "event": "gemini_call",
        "authorization": "Bearer secret-token-12345",
        "gemini_api_key": "AIzaSySecretKey",
        "jwt_secret_key": "supersecretkey",
        "password": "UserPass123!",
        "safe_param": "regular_value",
    }
    filtered = filter_sensitive_data(None, None, event)
    assert filtered["authorization"] == "[REDACTED]"
    assert filtered["gemini_api_key"] == "[REDACTED]"
    assert filtered["jwt_secret_key"] == "[REDACTED]"
    assert filtered["password"] == "[REDACTED]"
    assert filtered["safe_param"] == "regular_value"


@pytest.mark.asyncio
async def test_source_record_metadata_sanitization(
    client: AsyncClient,
    db_session: AsyncSession,
    researcher_headers: dict,
    admin_headers: dict,
):
    project = ResearchProject(
        id=str(uuid.uuid4()),
        name=f"Privacy Test Proj {uuid.uuid4().hex[:6]}",
        status="active",
    )
    db_session.add(project)
    await db_session.commit()

    record = SourceRecord(
        id=f"src_priv_{uuid.uuid4().hex[:6]}",
        project_id=project.id,
        source_platform="reddit",
        raw_content="Testing privacy redaction",
        author_handle="user_8f3a12b4",
        dedup_hash=f"hash_{uuid.uuid4().hex[:6]}",
        metadata_json={
            "subreddit": "googlephotos",
            "original_handle": "real_user_name_alice",
        },
    )
    db_session.add(record)
    await db_session.commit()

    # 1. Researcher fetching record does NOT see original_handle
    res_researcher = await client.get(
        f"/v1/projects/{project.id}/records/{record.id}",
        headers=researcher_headers,
    )
    assert res_researcher.status_code == 200
    res_data = res_researcher.json()
    assert res_data["author_handle"] == "user_8f3a12b4"
    assert "original_handle" not in res_data.get("metadata", {})

    # 2. Admin fetching record DOES see original_handle in metadata
    res_admin = await client.get(
        f"/v1/projects/{project.id}/records/{record.id}",
        headers=admin_headers,
    )
    assert res_admin.status_code == 200
    admin_data = res_admin.json()
    assert admin_data["metadata"]["original_handle"] == "real_user_name_alice"


@pytest.mark.asyncio
async def test_forum_adapter_robots_check():
    from backend.adapters.forum import ForumAdapter

    adapter = ForumAdapter()
    # Test robots check function doesn't crash on invalid/unreachable url
    allowed = await adapter.is_url_allowed_by_robots("https://example.com/test-forum")
    assert isinstance(allowed, bool)


import pytest
import os
import uuid
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from backend.database import Base, get_db
from backend.main import app
from backend.auth.jwt import create_access_token
import backend.models  # Register all models
from backend.gemini.client import get_gemini_client


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def override_get_db():
    async def _get_test_db():
        async with TestAsyncSessionLocal() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def enforce_gemini_mock_mode():
    client = get_gemini_client()
    orig = client.mock_mode
    client.mock_mode = True
    yield
    client.mock_mode = orig


@pytest.fixture
def admin_headers():
    token = create_access_token(
        {"sub": f"usr_admin_{uuid.uuid4().hex[:6]}", "email": "admin@google-photos.internal", "role": "admin", "name": "Admin User"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def researcher_headers():
    token = create_access_token(
        {"sub": f"usr_res_{uuid.uuid4().hex[:6]}", "email": "researcher@google-photos.internal", "role": "researcher", "name": "Researcher"}
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(researcher_headers):
    return researcher_headers


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


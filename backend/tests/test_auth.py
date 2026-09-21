import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.auth.jwt import create_access_token, decode_token


@pytest.mark.asyncio
async def test_jwt_token_encoding_and_decoding():
    data = {"sub": "usr_test", "email": "test@example.com", "role": "admin"}
    token = create_access_token(data)
    payload = decode_token(token)
    assert payload["sub"] == "usr_test"
    assert payload["email"] == "test@example.com"
    assert payload["role"] == "admin"
    assert "exp" in payload


@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/v1/auth/login",
            json={
                "email": "pm-lead@google-photos.internal",
                "password": "Password123!",
                "role": "admin",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "pm-lead@google-photos.internal"
        assert data["user"]["role"] == "admin"


@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/v1/auth/login",
            json={
                "email": "unknown-user@example.com",
                "password": "WrongPassword!",
            },
        )
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated():
    # Generate valid token
    token = create_access_token(
        {"sub": "usr_lead", "email": "pm-lead@google-photos.internal", "role": "admin", "name": "PM Lead"}
    )
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/auth/me", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "pm-lead@google-photos.internal"
        assert data["role"] == "admin"


@pytest.mark.asyncio
async def test_get_me_unauthorized():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/auth/me")
        assert response.status_code == 401

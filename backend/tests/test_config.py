import pytest
from backend.config import Settings


def test_default_config():
    settings = Settings(ENVIRONMENT="development", MOCK_DATA_MODE=True)
    assert settings.ENVIRONMENT == "development"
    assert settings.MOCK_DATA_MODE is True
    assert settings.PORT == 8000
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS


def test_cors_string_parsing():
    settings = Settings(
        ALLOWED_ORIGINS="http://localhost:3000, https://myapp.vercel.app"
    )
    assert "http://localhost:3000" in settings.ALLOWED_ORIGINS
    assert "https://myapp.vercel.app" in settings.ALLOWED_ORIGINS


def test_production_jwt_secret_validation():
    with pytest.raises(ValueError, match="JWT_SECRET_KEY must be a secure random secret"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="dev-insecure-short",
            GEMINI_API_KEY="test-key"
        )

import os
from functools import lru_cache
from typing import List, Union
from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings for the Photo Retrieval Discovery Engine.
    Reads from environment variables and/or .env file with fail-fast validation.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Server & Environment
    ENVIRONMENT: str = "development"  # "development", "staging", "production", "test"
    LOG_LEVEL: str = "INFO"
    MOCK_DATA_MODE: bool = False
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    APP_VERSION: str = "0.1.0"
    ALLOWED_ORIGINS: Union[str, List[str]] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://your-app.vercel.app"
    ]

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./discovery_engine.db"
    DB_ECHO: bool = False

    # Google Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"

    # Security & Auth
    JWT_SECRET_KEY: str = "dev-insecure-secret-key-change-in-production-min32chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 480  # 8 hours

    # Source Adapter Permissions
    ENABLE_RESTRICTED_SOURCES: bool = False

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if not v:
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["*"]

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def validate_cors_production(cls, v: List[str], info: ValidationInfo) -> List[str]:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if "*" in v or v == ["*"]:
                raise ValueError("In production mode, ALLOWED_ORIGINS cannot contain wildcard '*' for CORS security.")
        return v

    @field_validator("MOCK_DATA_MODE")
    @classmethod
    def validate_mock_mode_production(cls, v: bool, info: ValidationInfo) -> bool:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and v is True:
            raise ValueError("In production mode, MOCK_DATA_MODE cannot be enabled.")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url_production(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production" and "sqlite" in v:
            raise ValueError("In production mode, DATABASE_URL must be PostgreSQL with pgvector, not SQLite.")
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        if env == "production":
            if not v or "dev-insecure" in v or len(v) < 32:
                raise ValueError(
                    "In production, JWT_SECRET_KEY must be a secure random secret of at least 32 characters."
                )
        return v

    @field_validator("GEMINI_API_KEY")
    @classmethod
    def validate_gemini_key(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENVIRONMENT", "development")
        mock_mode = info.data.get("MOCK_DATA_MODE", False)
        if env == "production" and not mock_mode and not v:
            raise ValueError("In production mode, GEMINI_API_KEY is required unless MOCK_DATA_MODE=true.")
        return v


@lru_cache()
def get_settings() -> Settings:
    return Settings()

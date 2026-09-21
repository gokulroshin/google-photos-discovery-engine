import time
from fastapi import APIRouter
from backend.config import get_settings
from backend.database import check_database_health

router = APIRouter(tags=["Health"])

APP_START_TIME = time.time()


@router.get("/health")
async def health_check():
    """
    Health check endpoint returning system status, DB connectivity, Gemini status, version, and uptime.
    """
    settings = get_settings()
    db_healthy = await check_database_health()

    gemini_status = "mock_mode" if settings.MOCK_DATA_MODE else ("configured" if settings.GEMINI_API_KEY else "not_configured")
    uptime = round(time.time() - APP_START_TIME, 2)

    return {
        "status": "ok" if (db_healthy or settings.ENVIRONMENT == "development" or settings.MOCK_DATA_MODE) else "degraded",
        "environment": settings.ENVIRONMENT,
        "database": "connected" if db_healthy else "disconnected",
        "db_status": "ok" if db_healthy else "disconnected",
        "gemini": gemini_status,
        "gemini_status": gemini_status,
        "version": settings.APP_VERSION,
        "uptime": uptime,
        "uptime_seconds": uptime,
        "mock_mode": settings.MOCK_DATA_MODE,
    }


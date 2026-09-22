from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.config import get_settings
from backend.logger import setup_logging, logger
from backend.database import engine, Base
import backend.models  # Ensure all models are registered with Base metadata
from backend.routers import (
    health,
    auth,
    projects,
    source_records,
    ingestion_jobs,
    analysis,
    evidence,
    taxonomy,
    opportunities,
    reports,
    exports,
)



import time
import uuid

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        start_time = time.time()
        
        response = await call_next(request)
        
        duration_ms = (time.time() - start_time) * 1000.0
        response.headers["X-Request-ID"] = request_id
        
        # Exclude noisy polling / static health logs from flood if desired, but log standard requests
        if not request.url.path.startswith("/health") and not request.url.path.startswith("/docs"):
            logger.info(
                "http_request_finished",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                request_id=request_id,
            )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    setup_logging()
    settings = get_settings()
    logger.info(
        "Application starting",
        environment=settings.ENVIRONMENT,
        version=settings.APP_VERSION,
        mock_data_mode=settings.MOCK_DATA_MODE,
    )

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.warning("Database table initialization warning", error=str(e))

    yield
    # Shutdown
    logger.info("Application shutting down")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI-Powered Photo Retrieval Discovery Engine API",
        description="REST API for discovering, classifying, and comparing photo retrieval failure modes.",
        version=settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Security Headers Middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

    # CORS Middleware
    origins = settings.ALLOWED_ORIGINS
    is_wildcard = "*" in origins if isinstance(origins, list) else origins == "*"
    if is_wildcard:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Root route
    @app.get("/")
    async def root():
        return {
            "name": "Google Photos Discovery Engine API",
            "version": settings.APP_VERSION,
            "status": "healthy",
            "docs": "/docs",
        }

    # Health Check Endpoints
    app.include_router(health.router)
    app.include_router(health.router, prefix="/v1")

    # Authentication Endpoints
    app.include_router(auth.router)
    app.include_router(auth.router, prefix="/v1")

    # Projects Endpoints
    app.include_router(projects.router)
    app.include_router(projects.router, prefix="/v1")

    # Source Records Endpoints
    app.include_router(source_records.router)
    app.include_router(source_records.router, prefix="/v1")

    # Ingestion Jobs Endpoints
    app.include_router(ingestion_jobs.router)
    app.include_router(ingestion_jobs.router, prefix="/v1")

    # Analysis / Model Runs Endpoints
    app.include_router(analysis.router)
    app.include_router(analysis.router, prefix="/v1")

    # Evidence Records Endpoints
    app.include_router(evidence.router)
    app.include_router(evidence.router, prefix="/v1")

    # Taxonomy Problem Categories Endpoints
    app.include_router(taxonomy.router)
    app.include_router(taxonomy.router, prefix="/v1")

    # Opportunity Areas Endpoints
    app.include_router(opportunities.router)
    app.include_router(opportunities.router, prefix="/v1")

    # Research Reports Endpoints
    app.include_router(reports.router)
    app.include_router(reports.router, prefix="/v1")

    # Export Endpoints (Evidence & Taxonomy CSV/JSON)
    app.include_router(exports.router)
    app.include_router(exports.router, prefix="/v1")


    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", error=str(exc), path=request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please try again later."},
        )

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENVIRONMENT == "development",
    )

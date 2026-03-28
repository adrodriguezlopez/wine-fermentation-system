"""
Analysis Engine FastAPI Application Entry Point.

Provides REST API for:
- POST /api/v1/analyses           - Trigger fermentation analysis
- GET  /api/v1/analyses/{id}      - Retrieve analysis by ID
- GET  /api/v1/analyses/fermentation/{id} - List analyses for fermentation
- GET  /api/v1/recommendations/{id}       - Get recommendation by ID
- GET  /api/v1/fermentations/{id}/advisories       - List protocol advisories for a fermentation
- POST /api/v1/advisories/{id}/acknowledge          - Acknowledge a protocol advisory

Following ADR-006 API Layer Design and ADR-020 Analysis Engine Architecture.

Run with:
    uvicorn src.modules.analysis_engine.src.main:app --reload --port 8001
"""

import os

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# ADR-027: Structured Logging
from src.shared.wine_fermentator_logging import configure_logging, get_logger
from src.shared.wine_fermentator_logging.middleware import (
    LoggingMiddleware,
    UserContextMiddleware,
)

# Auth
from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import get_current_user

# ADR-026: Global domain error handlers
from src.shared.api.error_handlers import register_error_handlers

# Analysis Engine routers
from src.modules.analysis_engine.src.api.routers.analysis_router import router as analysis_router
from src.modules.analysis_engine.src.api.routers.recommendation_router import router as recommendation_router
from src.modules.analysis_engine.src.api.routers.advisory_router import router as advisory_router

from src.shared.infra.database.fastapi_session import initialize_database


configure_logging(log_level="INFO")
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure the Analysis Engine FastAPI application.

    Returns:
        Configured FastAPI instance with middleware and routers.
    """
    initialize_database()
    app = FastAPI(
        title="Wine Analysis Engine API",
        description=(
            "REST API for fermentation anomaly detection and recommendation generation. "
            "Part of the Wine Fermentation System."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ADR-027: Structured logging middleware
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(UserContextMiddleware)

    # ADR-026: Global RFC 7807 error handlers for DomainError subclasses
    register_error_handlers(app)

    # CORS — origins controlled by ALLOWED_ORIGINS env var
    _allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Analysis Engine routers
    app.include_router(analysis_router)
    app.include_router(recommendation_router)
    app.include_router(advisory_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        logger.debug("health_check_called")
        return {
            "status": "healthy",
            "service": "analysis-engine",
            "version": "1.0.0",
        }

    @app.get("/me", tags=["auth"])
    async def get_current_user_info(user: UserContext = Depends(get_current_user)):
        """Return authenticated user information."""
        logger.info("get_user_info", user_id=user.user_id, winery_id=user.winery_id)
        return {
            "user_id": user.user_id,
            "winery_id": user.winery_id,
            "email": user.email,
            "role": user.role.value,
        }

    logger.info("application_started", title=app.title, version=app.version)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.modules.analysis_engine.src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )

"""
FastAPI Application Entry Point - Fruit Origin Module

Provides REST API for managing vineyards, vineyard blocks, and harvest lots.

Endpoints:
    GET/POST /api/v1/vineyards               - Vineyard management
    GET/POST /api/v1/harvest-lots            - Harvest lot management

Following ADR-006 API Layer Design.

Run with:
    uvicorn src.modules.fruit_origin.src.main:app --reload --port 8002

Docker:
    docker-compose up fruit_origin
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ADR-027: Structured Logging Middleware
from src.shared.wine_fermentator_logging import configure_logging, get_logger
from src.shared.wine_fermentator_logging.middleware import (
    LoggingMiddleware,
    UserContextMiddleware,
)

# ADR-026: Domain error handlers (fruit_origin-specific)
from src.modules.fruit_origin.src.api_component.error_handlers import register_error_handlers

# Fruit Origin routers
from src.modules.fruit_origin.src.api_component.routers.vineyard_router import router as vineyard_router
from src.modules.fruit_origin.src.api_component.routers.harvest_lot_router import router as harvest_lot_router

from src.shared.auth.infra.api.auth_router import router as auth_router
from src.shared.api.constants import API_V1_PREFIX
from src.shared.infra.database.fastapi_session import close_database, initialize_database


# Configure structured logging before app creation
configure_logging(log_level="INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Initialise DB connection pool on startup; release it on shutdown."""
    initialize_database()
    logger.info("database_initialised")
    yield
    await close_database()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application for Fruit Origin module.

    Returns:
        Configured FastAPI instance with middleware and routers.
    """
    app = FastAPI(
        title="Fruit Origin API",
        description="API for managing vineyards, vineyard blocks, and harvest lots",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=_lifespan,
    )

    # ADR-027: Structured logging middleware.
    # Starlette wraps LIFO: the last add_middleware call is the outermost layer.
    # We want:  LoggingMiddleware (outer, runs first — clears ctx, binds
    #           correlation_id)  →  UserContextMiddleware (inner — decodes
    #           JWT and binds user_id/winery_id after the clear).
    # Therefore UserContextMiddleware is added first (inner) and
    # LoggingMiddleware is added last (outer).
    app.add_middleware(UserContextMiddleware)  # inner: runs after correlation bind
    app.add_middleware(LoggingMiddleware)       # outer: runs first, clears context

    # ADR-026: Register domain error handlers (RFC 7807 format)
    register_error_handlers(app)

    # CORS — origins controlled by ALLOWED_ORIGINS env var
    _allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    if _allowed_origins == ["*"]:
        logger.warning(
            "cors_wildcard_enabled",
            hint="Set ALLOWED_ORIGINS to a comma-separated list of explicit origins in staging/prod.",
        )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth endpoints (shared across all modules)
    app.include_router(auth_router, prefix=API_V1_PREFIX)

    # Fruit Origin routers — API version prefix centralised here
    app.include_router(vineyard_router, prefix=API_V1_PREFIX)       # /api/v1/vineyards
    app.include_router(harvest_lot_router, prefix=API_V1_PREFIX)    # /api/v1/harvest-lots

    # Health check
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring."""
        logger.debug("health_check_called")
        return {
            "status": "healthy",
            "service": "fruit_origin",
            "version": "1.0.0",
        }

    logger.info("fruit_origin_app_created", version="1.0.0")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    logger.info("starting_fruit_origin_server", port=8002)
    uvicorn.run(
        "src.modules.fruit_origin.src.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info",
    )

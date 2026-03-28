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

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# ADR-027: Structured Logging Middleware
from src.shared.wine_fermentator_logging import configure_logging, get_logger
from src.shared.wine_fermentator_logging.middleware import (
    LoggingMiddleware,
    UserContextMiddleware,
)

# Auth dependencies
from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import get_current_user

# ADR-026: Domain error handlers (fruit_origin-specific)
from src.modules.fruit_origin.src.api_component.error_handlers import register_error_handlers

# Fruit Origin routers
from src.modules.fruit_origin.src.api_component.routers.vineyard_router import router as vineyard_router
from src.modules.fruit_origin.src.api_component.routers.harvest_lot_router import router as harvest_lot_router

from src.shared.auth.infra.api.auth_router import router as auth_router
from src.shared.infra.database.fastapi_session import initialize_database


# Configure structured logging before app creation
configure_logging(log_level="INFO")
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application for Fruit Origin module.

    Returns:
        Configured FastAPI instance with middleware and routers.
    """
    initialize_database()
    app = FastAPI(
        title="Fruit Origin API",
        description="API for managing vineyards, vineyard blocks, and harvest lots",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth endpoints (shared across all modules)
    app.include_router(auth_router, prefix="/api/v1")

    # Fruit Origin routers — API version prefix centralised here
    app.include_router(vineyard_router, prefix="/api/v1")       # /api/v1/vineyards
    app.include_router(harvest_lot_router, prefix="/api/v1")    # /api/v1/harvest-lots

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

    # Auth info endpoint
    @app.get("/me", tags=["auth"])
    async def get_current_user_info(user: UserContext = Depends(get_current_user)):
        """Get current authenticated user information."""
        logger.info("get_user_info", user_id=user.user_id, winery_id=user.winery_id)
        return {
            "user_id": user.user_id,
            "winery_id": user.winery_id,
            "email": user.email,
            "role": user.role,
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

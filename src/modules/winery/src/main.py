"""
FastAPI Application Entry Point - Winery Module

Production FastAPI application with:
- ADR-027 Structured Logging & Observability
- Correlation ID tracking
- User context binding
- Winery admin API endpoints

Run with:
    uvicorn src.modules.winery.src.main:app --reload --port 8001
    
Docker:
    docker-compose up winery
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

# ADR-027: Structured Logging Middleware
from src.shared.wine_fermentator_logging import configure_logging, get_logger
from src.shared.wine_fermentator_logging.middleware import (
    LoggingMiddleware,
    UserContextMiddleware
)

# Auth dependencies
from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import get_current_user, require_admin

# ADR-026: Domain error handlers
from src.shared.api.error_handlers import register_error_handlers

# Winery router
from src.modules.winery.src.api_component.routers.winery_router import router as winery_router

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
    Create and configure FastAPI application for Winery module

    Returns:
        Configured FastAPI instance with middleware and routers
    """
    app = FastAPI(
        title="Winery Management API",
        description="API for managing winery organizations (multi-tenancy root)",
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
    
    # ADR-026: Register global error handlers for RFC 7807 format
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
    app.include_router(auth_router, prefix=API_V1_PREFIX)

    # Include winery router (admin namespace)
    app.include_router(winery_router, prefix=API_V1_PREFIX, tags=["wineries"])
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring"""
        logger.debug("health_check_called")
        return {
            "status": "healthy",
            "service": "winery",
            "version": "1.0.0"
        }
    
    # Test endpoint to verify auth works
    @app.get("/me", tags=["auth"])
    async def get_current_user_info(user: UserContext = Depends(get_current_user)):
        """Get current authenticated user information"""
        logger.info("get_user_info", user_id=user.user_id, winery_id=user.winery_id)
        return {
            "user_id": user.user_id,
            "winery_id": user.winery_id,
            "email": user.email,
            "role": user.role,
        }
    
    logger.info("winery_app_created", version="1.0.0")
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    logger.info("starting_winery_server", port=8001)
    uvicorn.run(
        "src.modules.winery.src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_config=None  # Use our structured logging instead
    )

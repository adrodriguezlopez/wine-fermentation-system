"""
FastAPI Application Entry Point

Production FastAPI application with:
- ADR-027 Structured Logging & Observability
- Correlation ID tracking
- User context binding
- API routers for fermentation and samples

Run with:
    uvicorn src.main:app --reload
    
Docker:
    docker-compose up fermentation
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware

from src.modules.fermentation.src.service_component.services.alert_scheduler_service import AlertSchedulerService

# ADR-027: Structured Logging Middleware
from src.shared.wine_fermentator_logging import configure_logging, get_logger
from src.shared.wine_fermentator_logging.middleware import (
    LoggingMiddleware,
    UserContextMiddleware
)

# Auth dependencies
from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker

# ADR-026: Domain error handlers
from src.shared.api.error_handlers import register_error_handlers

# Fermentation routers
from src.modules.fermentation.src.api.routers.fermentation_router import router as fermentation_router
from src.modules.fermentation.src.api.routers.sample_router import router as sample_router, samples_router

# Protocol routers (Phase 2)
from src.modules.fermentation.src.api.routers.protocol_router import router as protocol_router
from src.modules.fermentation.src.api.routers.protocol_step_router import router as protocol_step_router
from src.modules.fermentation.src.api.routers.protocol_execution_router import router as protocol_execution_router
from src.modules.fermentation.src.api.routers.step_completion_router import router as step_completion_router
from src.modules.fermentation.src.api.routers.alert_router import router as alert_router
from src.modules.fermentation.src.api.routers.action_router import router as action_router
from src.modules.fermentation.src.api.routers.historical_router import router as historical_router

from src.shared.auth.infra.api.auth_router import router as auth_router
from src.shared.infra.database.fastapi_session import initialize_database, close_database


# Configure structured logging before app creation
configure_logging(log_level="INFO")
logger = get_logger(__name__)


def _get_db_url() -> str:
    """Return the async DB URL for the scheduler (same source as DatabaseConfig)."""
    url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5433/wine_fermentation")
    # Normalise to asyncpg scheme
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Initialise DB and background scheduler on startup; clean up on shutdown."""
    initialize_database()
    logger.info("database_initialised")
    scheduler = AlertSchedulerService(
        database_url=_get_db_url(),
        interval_minutes=int(os.getenv("ALERT_SCHEDULER_INTERVAL_MINUTES", "30")),
    )
    scheduler.start()
    logger.info("alert_scheduler_wired")
    yield
    scheduler.stop()
    await close_database()


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI instance with middleware and routers
    """
    app = FastAPI(
        title="Wine Fermentation API",
        lifespan=_lifespan,
        description="API for managing wine fermentations and samples",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # ADR-027: Add structured logging middleware
    # Order matters: LoggingMiddleware should be outermost to capture all requests
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(UserContextMiddleware)
    
    # ADR-026: Register global error handlers for RFC 7807 format
    register_error_handlers(app)
    
    # CORS middleware — origins controlled by ALLOWED_ORIGINS env var
    # dev/test: default "*"; staging/prod: set to comma-separated list in .env
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

    # Include routers (sample router first for route specificity)
    # API version prefix centralised here — routers define only resource paths
    app.include_router(sample_router, prefix="/api/v1", tags=["samples"])
    app.include_router(samples_router, prefix="/api/v1", tags=["samples"])
    app.include_router(fermentation_router, prefix="/api/v1", tags=["fermentations"])
    
    # Protocol routers (Phase 2 API)
    app.include_router(protocol_router, prefix="/api/v1", tags=["protocols"])
    app.include_router(protocol_step_router, prefix="/api/v1", tags=["protocol-steps"])
    app.include_router(protocol_execution_router, prefix="/api/v1", tags=["protocol-executions"])
    app.include_router(step_completion_router, prefix="/api/v1", tags=["step-completions"])
    app.include_router(alert_router, prefix="/api/v1", tags=["protocol-alerts"])
    app.include_router(action_router, prefix="/api/v1", tags=["winemaker-actions"])
    app.include_router(historical_router, prefix="/api/v1")  # ADR-032: /api/v1/fermentation/historical
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint for monitoring"""
        logger.debug("health_check_called")
        return {
            "status": "healthy",
            "service": "fermentation",
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
            "role": user.role.value
        }
    
    logger.info("application_started", title=app.title, version=app.version)
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    # Run with: python -m src.main
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

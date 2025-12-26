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
from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker

# ADR-026: Domain error handlers
from shared.api.error_handlers import register_error_handlers

# Fermentation routers
from src.modules.fermentation.src.api.routers.fermentation_router import router as fermentation_router
from src.modules.fermentation.src.api.routers.sample_router import router as sample_router, samples_router


# Configure structured logging before app creation
configure_logging(log_level="INFO")
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application
    
    Returns:
        Configured FastAPI instance with middleware and routers
    """
    app = FastAPI(
        title="Wine Fermentation API",
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
    
    # CORS middleware (configure for production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO: Configure allowed origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers (sample router first for route specificity)
    app.include_router(sample_router, tags=["samples"])
    app.include_router(samples_router, tags=["samples"])
    app.include_router(fermentation_router, tags=["fermentations"])
    
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

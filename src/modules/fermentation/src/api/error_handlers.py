"""
Error Handlers for FastAPI endpoints

ADR-026: Updated to use shared domain exception hierarchy with RFC 7807 format.
Centralizes exception handling for API endpoints to reduce code duplication
and ensure consistent error responses.

Following DRY principle and ADR-006 API Layer Design.

Implements ADR-027 Structured Logging:
- Logs all exceptions with context
- Correlation IDs in error responses
- Error types for monitoring/alerting
"""

from fastapi import HTTPException, status
from typing import Callable, TypeVar, Any
from functools import wraps

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger

# ADR-026: Import shared domain errors (preferred over legacy errors)
from shared.domain.errors import (
    DomainError,
    FermentationError,
    FermentationNotFound,
    InvalidFermentationState,
    FermentationAlreadyCompleted,
    SampleNotFound,
    InvalidSampleDate,
    InvalidSampleValue
)

# Legacy imports for backward compatibility
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleViolation
)

logger = get_logger(__name__)


T = TypeVar('T')


def handle_service_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle common service layer exceptions in API endpoints.
    
    ADR-026: Now handles DomainError exceptions with RFC 7807 format.
    The error handler will be automatically invoked by FastAPI's global
    exception handler (registered in main.py).
    
    For backward compatibility, also handles legacy service layer exceptions:
    - ValidationError -> 400 Bad Request / 422 Unprocessable Entity
    - NotFoundError -> 404 Not Found
    - DuplicateError -> 409 Conflict
    - BusinessRuleViolation -> 422 Unprocessable Entity
    - Exception -> 500 Internal Server Error
    
    Usage:
        @router.get("/items/{id}")
        @handle_service_errors
        async def get_item(id: int):
            return await service.get_item(id)
    
    Note: DomainError exceptions are re-raised to be handled by global handler.
          HTTPException is also re-raised as-is to preserve custom responses.
    
    Status: ✅ Updated for ADR-026 (2025-12-26)
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
        except DomainError:
            # Re-raise DomainError to be handled by global RFC 7807 handler
            raise
        except HTTPException:
            # Re-raise FastAPI HTTPException as-is
            raise
        except NotFoundError as e:
            logger.warning(
                "api_not_found_error",
                error_message=str(e),
                error_type="NotFoundError",
                endpoint=func.__name__
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        except ValidationError as e:
            logger.warning(
                "api_validation_error",
                error_message=str(e),
                error_type="ValidationError",
                endpoint=func.__name__
            )
            # Use 422 for validation errors (semantic errors)
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        except DuplicateError as e:
            logger.warning(
                "api_duplicate_error",
                error_message=str(e),
                error_type="DuplicateError",
                endpoint=func.__name__
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        except BusinessRuleViolation as e:
            logger.warning(
                "api_business_rule_violation",
                error_message=str(e),
                error_type="BusinessRuleViolation",
                endpoint=func.__name__
            )
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )
        except Exception as e:
            logger.error(
                "api_unexpected_error",
                error_message=str(e),
                error_type=type(e).__name__,
                endpoint=func.__name__
            )
            # Catch-all for unexpected errors
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}"
            )
    
    return wrapper


def register_error_handlers(app) -> None:
    """
    Register exception handlers with FastAPI app for Fermentation domain errors.
    
    Maps domain errors to appropriate HTTP status codes:
    - FermentationNotFound → 404
    - SampleNotFound → 404
    - InvalidFermentationState → 422
    - FermentationAlreadyCompleted → 409
    - InvalidSampleDate, InvalidSampleValue → 422
    
    Args:
        app: FastAPI application instance
    """
    from fastapi import Request, status
    from fastapi.responses import JSONResponse
    
    @app.exception_handler(FermentationNotFound)
    async def fermentation_not_found_handler(
        request: Request,
        exc: FermentationNotFound
    ) -> JSONResponse:
        """Handle fermentation not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "FermentationNotFound"}
        )
    
    @app.exception_handler(SampleNotFound)
    async def sample_not_found_handler(
        request: Request,
        exc: SampleNotFound
    ) -> JSONResponse:
        """Handle sample not found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc), "error_type": "SampleNotFound"}
        )
    
    @app.exception_handler(InvalidFermentationState)
    async def invalid_fermentation_state_handler(
        request: Request,
        exc: InvalidFermentationState
    ) -> JSONResponse:
        """Handle invalid fermentation state errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "InvalidFermentationState"}
        )
    
    @app.exception_handler(FermentationAlreadyCompleted)
    async def fermentation_already_completed_handler(
        request: Request,
        exc: FermentationAlreadyCompleted
    ) -> JSONResponse:
        """Handle fermentation already completed errors."""
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc), "error_type": "FermentationAlreadyCompleted"}
        )
    
    @app.exception_handler(InvalidSampleDate)
    async def invalid_sample_date_handler(
        request: Request,
        exc: InvalidSampleDate
    ) -> JSONResponse:
        """Handle invalid sample date errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "InvalidSampleDate"}
        )
    
    @app.exception_handler(InvalidSampleValue)
    async def invalid_sample_value_handler(
        request: Request,
        exc: InvalidSampleValue
    ) -> JSONResponse:
        """Handle invalid sample value errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": str(exc), "error_type": "InvalidSampleValue"}
        )

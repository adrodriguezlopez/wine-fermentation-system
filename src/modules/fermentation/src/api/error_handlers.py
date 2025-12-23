"""
Error Handlers for FastAPI endpoints

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
    
    Converts service layer exceptions to appropriate HTTP responses:
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
    
    Note: HTTPException is re-raised as-is to preserve custom HTTP responses.
    
    Status: ✅ Implemented (2025-11-15)
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)
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

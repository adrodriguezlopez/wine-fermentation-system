"""
Error Handlers for Analysis Engine API endpoints.

Centralizes exception handling so routers stay clean.
Re-raises DomainError to be caught by the global RFC 7807 handler (ADR-026).
Converts legacy service exceptions to appropriate HTTPException.

Following same pattern as fermentation module's error_handlers.py.
"""

from fastapi import HTTPException, status
from typing import Any, Callable, TypeVar
from functools import wraps

from src.shared.wine_fermentator_logging import get_logger
from src.shared.domain.errors import DomainError, CrossWineryAccessDenied

logger = get_logger(__name__)

T = TypeVar("T")


def handle_service_errors(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to handle common service layer exceptions in Analysis Engine endpoints.

    - DomainError  → re-raised (caught by global RFC 7807 handler in main.py)
    - HTTPException → re-raised as-is
    - CrossWineryAccessDenied → 403 Forbidden
    - ValueError → 400 Bad Request
    - Exception → 500 Internal Server Error

    Usage:
        @router.post("/analyses")
        @handle_service_errors
        async def trigger_analysis(request: AnalysisCreateRequest, ...):
            ...
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        try:
            return await func(*args, **kwargs)

        except CrossWineryAccessDenied as e:
            logger.warning(
                "analysis_cross_winery_access_denied",
                error_message=str(e),
                endpoint=func.__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(e),
            )

        except DomainError:
            # Re-raise to global RFC 7807 handler
            raise

        except HTTPException:
            # Preserve explicitly raised HTTP exceptions
            raise

        except ValueError as e:
            logger.warning(
                "analysis_value_error",
                error_message=str(e),
                endpoint=func.__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        except Exception as e:
            logger.error(
                "analysis_unexpected_error",
                error_message=str(e),
                error_type=type(e).__name__,
                endpoint=func.__name__,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"An unexpected error occurred: {str(e)}",
            )

    return wrapper

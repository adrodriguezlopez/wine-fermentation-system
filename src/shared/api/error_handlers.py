"""
FastAPI error handlers for domain exceptions.

Implements ADR-026: Error Handling & Exception Hierarchy Strategy.
Provides RFC 7807 Problem Details format with ADR-027 structured logging.
"""

from typing import Any, Dict

from fastapi import Request
from fastapi.responses import JSONResponse

from domain.errors import DomainError
from wine_fermentator_logging import get_logger

logger = get_logger(__name__)


def register_error_handlers(app: Any) -> None:
    """
    Register all error handlers with FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_exception_handler(DomainError, domain_error_handler)


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    """
    Global handler for all domain errors.
    
    Implements RFC 7807 Problem Details format:
    https://datatracker.ietf.org/doc/html/rfc7807
    
    Args:
        request: FastAPI request object
        exc: Domain exception instance
        
    Returns:
        JSONResponse with RFC 7807 format and appropriate HTTP status
    """
    # Log error with ADR-027 structured logging
    logger.warning(
        "domain_error_occurred",
        error_type=exc.__class__.__name__,
        error_code=exc.error_code,
        message=exc.message,
        context=exc.context,
        path=str(request.url.path),
        http_status=exc.http_status
    )
    
    # Build RFC 7807 Problem Details response
    error_response: Dict[str, Any] = {
        # Type URI that identifies the problem type
        "type": f"https://api.wine-fermentation.com/errors/{exc.error_code.lower()}",
        
        # Short, human-readable title
        "title": _format_error_title(exc.__class__.__name__),
        
        # HTTP status code
        "status": exc.http_status,
        
        # Human-readable explanation specific to this occurrence
        "detail": exc.message,
        
        # URI reference identifying this specific occurrence
        "instance": str(request.url.path),
        
        # Machine-readable error code for frontend
        "code": exc.error_code,
    }
    
    # Include additional context (field names, IDs, etc.)
    error_response.update(exc.context)
    
    return JSONResponse(
        status_code=exc.http_status,
        content=error_response
    )


def _format_error_title(class_name: str) -> str:
    """
    Convert PascalCase exception name to human-readable title.
    
    Examples:
        FermentationNotFound -> Fermentation Not Found
        InvalidHarvestDate -> Invalid Harvest Date
        
    Args:
        class_name: Exception class name
        
    Returns:
        Formatted title string
    """
    # Insert space before capital letters
    result = []
    for i, char in enumerate(class_name):
        if char.isupper() and i > 0:
            result.append(" ")
        result.append(char)
    
    return "".join(result)

"""
Structured logging infrastructure for Wine Fermentation System.

Provides centralized, structured logging with:
- JSON output for production (easy parsing by log aggregators)
- Human-readable console output for development
- Automatic correlation ID tracking across requests
- Context propagation (winery_id, user_id, etc.)
- Performance timing utilities

Usage:
    from src.shared.wine_fermentator_logging import get_logger, LogTimer, configure_logging
    
    # Configure once at app startup
    configure_logging(environment="production", json_logs=True)
    
    # Use in any module
    logger = get_logger(__name__)
    logger.info("event_name", key1="value1", key2="value2")
    
    # Time operations
    with LogTimer(logger, "operation_name"):
        result = expensive_function()

Related ADRs:
- ADR-027: Structured Logging & Observability Infrastructure
"""

from .logger import (
    configure_logging,
    get_logger,
    LogTimer,
    sanitize_log_data,
)

# Conditional import of middleware (requires FastAPI)
try:
    from .middleware import (
        LoggingMiddleware,
        UserContextMiddleware,
        get_correlation_id,
    )
    _middleware_available = True
except ImportError:
    # FastAPI not installed, middleware not available
    _middleware_available = False
    LoggingMiddleware = None
    UserContextMiddleware = None
    get_correlation_id = None

__all__ = [
    # Logger configuration and utilities (always available)
    "configure_logging",
    "get_logger",
    "LogTimer",
    "sanitize_log_data",
]

# Add middleware to exports only if available
if _middleware_available:
    __all__.extend([
        "LoggingMiddleware",
        "UserContextMiddleware",
        "get_correlation_id",
    ])

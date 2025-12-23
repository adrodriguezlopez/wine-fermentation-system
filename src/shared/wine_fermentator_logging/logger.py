"""
Core logging configuration for Wine Fermentation System.

Provides structured logging using structlog with:
- JSON output for production (parseable by CloudWatch, ELK, Datadog)
- Human-readable console output for development
- Automatic timestamp, log level, and context binding
- Performance timing utilities
- Exception tracking with stack traces

Key Features:
- Correlation ID propagation across request lifecycle
- Context variables (winery_id, user_id) automatically included
- Configurable log levels by environment
- Thread-safe and async-compatible

Related ADR: ADR-027 (Structured Logging & Observability)
"""

import structlog
import logging
import sys
import time
from typing import Optional
from contextvars import ContextVar


# Context variable for storing additional logging context
# This allows automatic propagation of winery_id, user_id, etc.
_logging_context: ContextVar[dict] = ContextVar("logging_context", default={})


def configure_logging(
    environment: str = "development",
    log_level: str = "INFO",
    json_logs: bool = None,
) -> None:
    """
    Configure structlog for the entire application.
    
    This should be called ONCE at application startup (e.g., in main.py).
    
    Args:
        environment: "development" or "production"
            - development: Human-readable console output with colors
            - production: JSON output for log aggregators
        log_level: Minimum log level to output
            - "DEBUG": Verbose output, all details
            - "INFO": Normal operations, audit trail (default)
            - "WARNING": Recoverable issues, validation failures
            - "ERROR": Unexpected errors, system failures
        json_logs: Override JSON output
            - None: Auto-detect (JSON in production, console in dev)
            - True: Force JSON output
            - False: Force console output
    
    Example:
        # In main.py or app startup
        from src.shared.logging import configure_logging
        
        configure_logging(
            environment="production",
            log_level="INFO",
            json_logs=True
        )
    
    Environment Variables:
        LOG_LEVEL: Override log level (DEBUG, INFO, WARNING, ERROR)
        LOG_FORMAT: Override format (json, console)
    """
    
    # Auto-detect JSON output if not specified
    if json_logs is None:
        json_logs = environment == "production"
    
    # Build processor pipeline
    processors = [
        # Merge context variables (correlation_id, winery_id, etc.)
        structlog.contextvars.merge_contextvars,
        
        # Add log level to output
        structlog.stdlib.add_log_level,
        
        # Add timestamp in ISO 8601 format
        structlog.processors.TimeStamper(fmt="iso"),
        
        # Format stack info on exceptions
        structlog.processors.StackInfoRenderer(),
        
        # Format exception info (traceback)
        structlog.processors.format_exc_info,
        
        # Render as JSON (production) or colored console (development)
        structlog.processors.JSONRenderer() if json_logs
        else structlog.dev.ConsoleRenderer(colors=True, pad_event_to=30)
    ]
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(log_level.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )
    
    # Also configure stdlib logging (for libraries that use it)
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.getLevelName(log_level.upper()),
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a configured logger instance for a module.
    
    This is the primary way to get a logger in your code.
    The logger automatically includes all context variables bound
    via structlog.contextvars.bind_contextvars().
    
    Args:
        name: Logger name, typically __name__ of the module
    
    Returns:
        Configured structlog BoundLogger instance
    
    Usage:
        # At the top of your module
        from src.shared.wine_fermentator_logging import get_logger
        
        logger = get_logger(__name__)
        
        # In your code
        logger.info("operation_completed", entity_id=123, status="success")
        
        # With context binding (appears in ALL subsequent logs)
        import structlog
        structlog.contextvars.bind_contextvars(winery_id="abc123")
        
        logger.info("event")  # Automatically includes winery_id=abc123
    
    Log Levels:
        logger.debug("event", ...)    # Verbose development details
        logger.info("event", ...)     # Normal operations, audit trail
        logger.warning("event", ...)  # Recoverable issues, validation failures
        logger.error("event", ...)    # Unexpected errors, system failures
    
    Best Practices:
        - Use structured logging: logger.info("event", key=value)
        - NOT string formatting: logger.info(f"Event: {value}")
        - Event names: lowercase_with_underscores
        - Include relevant IDs: entity_id, winery_id, user_id
        - Add exc_info=True for errors with stack traces
    """
    return structlog.get_logger(name)


class LogTimer:
    """
    Context manager for logging operation execution time.
    
    Automatically logs when operation starts and completes (or fails),
    including the duration in milliseconds.
    
    Usage:
        from src.shared.wine_fermentator_logging import get_logger, LogTimer
        
        logger = get_logger(__name__)
        
        # Measure and log execution time
        with LogTimer(logger, "database_query"):
            result = await session.execute(query)
        
        # Logs automatically:
        # {
        #   "event": "database_query_completed",
        #   "operation": "database_query",
        #   "duration_ms": 45.67,
        #   "status": "success",
        #   "timestamp": "2025-12-16T10:30:45.123Z"
        # }
        
        # On exception:
        # {
        #   "event": "database_query_failed",
        #   "operation": "database_query",
        #   "duration_ms": 23.45,
        #   "status": "error",
        #   "error_type": "OperationalError"
        # }
    
    Attributes:
        logger: The logger to use for timing logs
        operation: Name of the operation being timed
        log_start: Whether to log when operation starts (default: False)
    """
    
    def __init__(
        self,
        logger: structlog.BoundLogger,
        operation: str,
        log_start: bool = False,
    ):
        """
        Initialize LogTimer.
        
        Args:
            logger: Logger instance to use for timing logs
            operation: Name of the operation (e.g., "db_query", "validation")
            log_start: If True, log when operation starts (default: False)
        """
        self.logger = logger
        self.operation = operation
        self.log_start = log_start
        self.start_time: Optional[float] = None
    
    def __enter__(self):
        """Start timing and optionally log operation start."""
        self.start_time = time.perf_counter()
        
        if self.log_start:
            self.logger.debug(
                f"{self.operation}_started",
                operation=self.operation,
            )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log operation completion with duration."""
        if self.start_time is None:
            return
        
        # Calculate elapsed time in milliseconds
        elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        
        if exc_type is None:
            # Success: log completion
            self.logger.info(
                f"{self.operation}_completed",
                operation=self.operation,
                duration_ms=round(elapsed_ms, 2),
                status="success",
            )
        else:
            # Failure: log error
            self.logger.error(
                f"{self.operation}_failed",
                operation=self.operation,
                duration_ms=round(elapsed_ms, 2),
                status="error",
                error_type=exc_type.__name__ if exc_type else "Unknown",
            )


def sanitize_log_data(data: dict, sensitive_keys: list[str] = None) -> dict:
    """
    Remove sensitive information from data before logging.
    
    Use this to sanitize user input, API responses, or any data that
    might contain passwords, tokens, or PII before logging.
    
    Args:
        data: Dictionary to sanitize
        sensitive_keys: Additional keys to redact (beyond defaults)
    
    Returns:
        Sanitized copy of the data dictionary
    
    Default sensitive keys:
        - password
        - token
        - secret
        - api_key
        - authorization
        - credit_card
        - ssn
    
    Usage:
        from src.shared.wine_fermentator_logging import get_logger, sanitize_log_data
        
        logger = get_logger(__name__)
        
        user_data = {
            "username": "john",
            "password": "secret123",  # Will be redacted
            "email": "john@example.com"
        }
        
        logger.info(
            "user_created",
            user_data=sanitize_log_data(user_data)
        )
        
        # Logs: {"username": "john", "password": "***REDACTED***", "email": "..."}
    """
    # Default sensitive keys
    default_sensitive = {
        "password",
        "token",
        "secret",
        "api_key",
        "authorization",
        "credit_card",
        "ssn",
        "jwt",
        "refresh_token",
        "access_token",
    }
    
    # Merge with custom sensitive keys
    if sensitive_keys:
        default_sensitive.update(key.lower() for key in sensitive_keys)
    
    # Create sanitized copy
    sanitized = {}
    for key, value in data.items():
        if key.lower() in default_sensitive:
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_log_data(value, sensitive_keys)
        else:
            sanitized[key] = value
    
    return sanitized


# Example usage and testing
if __name__ == "__main__":
    """
    Run this file directly to test logging configuration.
    
    Usage:
        python -m src.shared.wine_fermentator_logging.logger
    """
    print("Testing structured logging configuration...\n")
    
    # Test development mode (console output)
    print("=== Development Mode (Console) ===")
    configure_logging(environment="development", log_level="DEBUG")
    logger = get_logger("test_module")
    
    logger.debug("debug_message", detail="verbose information")
    logger.info("info_message", user_id=123, action="login")
    logger.warning("warning_message", validation="failed")
    logger.error("error_message", error="something went wrong")
    
    # Test context binding
    print("\n=== Context Binding Test ===")
    structlog.contextvars.bind_contextvars(
        correlation_id="req-123",
        winery_id="winery-456"
    )
    logger.info("request_processed", status="success")
    
    # Test LogTimer
    print("\n=== LogTimer Test ===")
    with LogTimer(logger, "test_operation"):
        import time
        time.sleep(0.1)  # Simulate work
    
    # Test error logging
    print("\n=== Error Logging Test ===")
    try:
        with LogTimer(logger, "failing_operation"):
            raise ValueError("Test error")
    except ValueError:
        pass
    
    # Test production mode (JSON)
    print("\n=== Production Mode (JSON) ===")
    configure_logging(environment="production", json_logs=True)
    logger = get_logger("test_module")
    
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        correlation_id="req-789",
        winery_id="winery-abc"
    )
    
    logger.info(
        "fermentation_created",
        fermentation_id="ferm-123",
        variety="Malbec",
        winery_id="winery-abc",
    )
    
    # Test sanitization
    print("\n=== Sanitization Test ===")
    user_data = {
        "username": "john",
        "password": "secret123",
        "email": "john@example.com",
        "nested": {
            "token": "abc123",
            "public_data": "visible"
        }
    }
    
    logger.info(
        "user_data_logged",
        original=user_data,
        sanitized=sanitize_log_data(user_data)
    )
    
    print("\n✅ Logging tests completed!")

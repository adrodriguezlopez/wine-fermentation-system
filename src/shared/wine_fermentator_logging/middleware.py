"""
FastAPI middleware for request correlation and structured logging.

Automatically adds correlation IDs to all requests and provides
request/response logging with timing metrics.

Features:
- Generates unique correlation_id for each request
- Binds correlation_id to structlog context (available in all logs)
- Logs request start/end with method, path, status code
- Measures and logs request duration
- Adds X-Correlation-ID header to responses for debugging
- Binds request metadata to context (method, path, client_host)

Related ADR: ADR-027 (Structured Logging & Observability)
"""

import os
import uuid
import time
from typing import Callable
import jwt
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from .logger import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add correlation IDs and log all HTTP requests.
    
    This middleware should be added to the FastAPI app during initialization.
    It provides:
    - Automatic correlation ID generation per request
    - Request/response logging with timing
    - Context propagation (correlation_id available in all logs)
    - Response headers with correlation ID for debugging
    
    Usage:
        from fastapi import FastAPI
        from src.shared.wine_fermentator_logging import LoggingMiddleware, configure_logging
        
        app = FastAPI()
        
        # Configure logging first
        configure_logging(environment="production")
        
        # Add middleware
        app.add_middleware(LoggingMiddleware)
        
        # Now all requests will have correlation IDs and logging
    
    What gets logged:
        - request_started: When request begins processing
        - request_completed: When request finishes successfully
        - request_failed: When request errors (with exception info)
    
    What gets bound to context (available in ALL logs during request):
        - correlation_id: Unique ID for this request
        - path: Request path (e.g., "/api/v1/fermentations")
        - method: HTTP method (GET, POST, etc.)
        - client_host: Client IP address (if available)
    
    Response headers added:
        - X-Correlation-ID: The correlation ID for debugging
    
    Example log output (JSON):
        {
          "event": "request_completed",
          "correlation_id": "123e4567-e89b-12d3-a456-426614174000",
          "path": "/api/v1/fermentations",
          "method": "POST",
          "status_code": 201,
          "duration_ms": 78.9,
          "client_host": "192.168.1.100",
          "timestamp": "2025-12-16T10:30:45.123Z",
          "level": "info"
        }
    """
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: list[str] = None,
    ):
        """
        Initialize logging middleware.
        
        Args:
            app: The FastAPI application instance
            exclude_paths: List of paths to exclude from logging
                          (e.g., ["/health", "/metrics"])
                          Default: ["/health", "/docs", "/redoc", "/openapi.json"]
        """
        super().__init__(app)
        
        # Default paths to exclude from logging (health checks, docs)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/healthz",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]
    
    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Process request with logging and correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/handler in the chain
        
        Returns:
            HTTP response with X-Correlation-ID header
        """
        # Skip logging for excluded paths (health checks, docs)
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Generate unique correlation ID for this request
        correlation_id = str(uuid.uuid4())
        
        # Clear any previous context and bind new context
        # This makes correlation_id, path, method available in ALL logs
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=request.url.path,
            method=request.method,
        )
        
        # Extract client information
        client_host = None
        if request.client:
            client_host = request.client.host
        
        # Log request start
        start_time = time.perf_counter()
        logger.info(
            "request_started",
            path=request.url.path,
            method=request.method,
            client_host=client_host,
            query_params=dict(request.query_params) if request.query_params else None,
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log successful request completion
            logger.info(
                "request_completed",
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            
            # Add correlation ID to response headers (useful for debugging)
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Calculate duration even on error
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # Log failed request
            logger.error(
                "request_failed",
                path=request.url.path,
                method=request.method,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2),
                exc_info=True,  # Include full stack trace
            )
            
            # Re-raise to let error handlers deal with it
            raise


class UserContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to bind authenticated user context to structlog contextvars.

    Decodes the JWT from the ``Authorization: Bearer <token>`` header using
    the application secret key (``JWT_SECRET_KEY`` env var).  The decode is
    best-effort: any failure (missing header, expired token, wrong key,
    malformed token) is silently swallowed and the request continues
    unaffected.

    This middleware must be registered *before* ``LoggingMiddleware`` with
    ``app.add_middleware`` so that Starlette's LIFO wrapping makes
    ``LoggingMiddleware`` the outermost layer (runs first, clears context,
    binds ``correlation_id``) and this middleware the inner layer (runs
    second, adds ``user_id`` / ``winery_id`` / ``user_role`` after the
    clear).

    Security enforcement is **not** the responsibility of this middleware —
    the ``get_current_user`` FastAPI dependency handles that and also calls
    ``bind_contextvars`` with the validated ``UserContext`` as a definitive
    binding inside the route handler.

    What gets bound to context (when a valid JWT is present):
        - ``user_id``   – JWT ``sub`` claim (str)
        - ``winery_id`` – JWT ``winery_id`` claim (str)
        - ``user_role`` – JWT ``role`` claim (str)

    Example log output:
        {"event": "fermentation_created", "correlation_id": "abc",
         "user_id": "42", "winery_id": "7", "user_role": "winemaker", ...}
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        """
        Decode JWT from Authorization header and bind user context to logs.

        Best-effort: silently skips if the header is absent, the token is
        malformed, expired, or signed with a different key.  Security
        enforcement is handled by the ``get_current_user`` dependency.
        """
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[len("Bearer "):]
            try:
                secret = os.environ.get("JWT_SECRET_KEY")
                if not secret:
                    # JWT_SECRET_KEY not configured — skip user-context binding.
                    # Security enforcement is handled by the get_current_user dependency.
                    return await call_next(request)
                payload = jwt.decode(
                    token,
                    secret,
                    algorithms=["HS256"],
                )
                structlog.contextvars.bind_contextvars(
                    user_id=str(payload.get("sub", "")),
                    winery_id=str(payload.get("winery_id", "")),
                    user_role=payload.get("role", ""),
                )
            except Exception:
                # Invalid, expired, or malformed token — skip silently.
                # The auth dependency will reject the request if needed.
                pass

        return await call_next(request)


# Helper function for manual correlation ID management
def get_correlation_id() -> str:
    """
    Get the current request's correlation ID.
    
    Useful for:
    - Adding correlation ID to custom headers
    - Including in error responses
    - Logging in background tasks
    
    Returns:
        Correlation ID string, or "unknown" if not in request context
    
    Usage:
        from src.shared.wine_fermentator_logging import get_correlation_id
        
        # In an endpoint or background task
        correlation_id = get_correlation_id()
        
        # Use in custom response
        return JSONResponse(
            content={"data": result},
            headers={"X-Correlation-ID": correlation_id}
        )
    """
    try:
        # Try to get from structlog context
        import structlog
        context = structlog.contextvars.get_contextvars()
        return context.get("correlation_id", "unknown")
    except Exception:
        return "unknown"


# Example usage
if __name__ == "__main__":
    """
    Test the middleware (requires FastAPI).
    
    Usage:
        python -m src.shared.wine_fermentator_logging.middleware
    """
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    from .logger import configure_logging
    
    # Configure logging
    configure_logging(environment="development", log_level="DEBUG")
    
    # Create FastAPI app
    app = FastAPI(title="Logging Middleware Test")
    
    # Add middleware
    app.add_middleware(LoggingMiddleware)
    
    # Test endpoint
    @app.get("/test")
    async def test_endpoint():
        """Test endpoint that uses logger."""
        logger = get_logger(__name__)
        logger.info("test_endpoint_called", message="Hello from test endpoint")
        return {"message": "Check the logs!"}
    
    @app.get("/error")
    async def error_endpoint():
        """Test endpoint that raises an error."""
        logger = get_logger(__name__)
        logger.warning("about_to_raise_error")
        raise ValueError("Test error for logging")
    
    print("Middleware test app created.")
    print("Run with: uvicorn src.shared.wine_fermentator_logging.middleware:app --reload")
    print("\nTest endpoints:")
    print("  http://localhost:8000/test")
    print("  http://localhost:8000/error")

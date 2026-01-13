"""
Unit tests for API error handlers.

Tests the handle_service_errors decorator and register_error_handlers function
to ensure proper exception handling and HTTP status code mapping.

ADR-026: Tests both DomainError exceptions (RFC 7807) and legacy exceptions.
ADR-033: Phase 1 - API Layer coverage improvement.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse

# Add paths for imports (same as test_sample_router.py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "shared"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent.parent.parent / "src"))

from src.modules.fermentation.src.api.error_handlers import handle_service_errors, register_error_handlers

# Domain errors (ADR-026)
from shared.domain.errors import (
    DomainError,
    FermentationNotFound,
    SampleNotFound,
    InvalidFermentationState,
    FermentationAlreadyCompleted,
    InvalidSampleDate,
    InvalidSampleValue
)

# Legacy errors
from src.modules.fermentation.src.service_component.errors import (
    ValidationError,
    NotFoundError,
    DuplicateError,
    BusinessRuleViolation
)


# ==================== Tests for handle_service_errors decorator ====================


@pytest.mark.asyncio
async def test_handle_service_errors_success():
    """Should return result when no exception is raised."""
    
    @handle_service_errors
    async def success_func():
        return {"status": "ok"}
    
    result = await success_func()
    assert result == {"status": "ok"}


@pytest.mark.asyncio
async def test_handle_service_errors_reraises_domain_error():
    """Should re-raise DomainError to be handled by global handler."""
    
    @handle_service_errors
    async def domain_error_func():
        raise FermentationNotFound(message="Fermentation not found", fermentation_id=123)
    
    with pytest.raises(FermentationNotFound) as exc_info:
        await domain_error_func()
    
    assert exc_info.value.context["fermentation_id"] == 123


@pytest.mark.asyncio
async def test_handle_service_errors_reraises_http_exception():
    """Should re-raise HTTPException as-is."""
    
    @handle_service_errors
    async def http_error_func():
        raise HTTPException(status_code=403, detail="Forbidden")
    
    with pytest.raises(HTTPException) as exc_info:
        await http_error_func()
    
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden"


@pytest.mark.asyncio
async def test_handle_service_errors_not_found_error():
    """Should convert NotFoundError to 404 HTTPException."""
    
    @handle_service_errors
    async def not_found_func():
        raise NotFoundError("Resource not found")
    
    with pytest.raises(HTTPException) as exc_info:
        await not_found_func()
    
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == "Resource not found"


@pytest.mark.asyncio
async def test_handle_service_errors_validation_error():
    """Should convert ValidationError to 422 HTTPException."""
    
    @handle_service_errors
    async def validation_error_func():
        raise ValidationError("Invalid input")
    
    with pytest.raises(HTTPException) as exc_info:
        await validation_error_func()
    
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc_info.value.detail == "Invalid input"


@pytest.mark.asyncio
async def test_handle_service_errors_duplicate_error():
    """Should convert DuplicateError to 409 HTTPException."""
    
    @handle_service_errors
    async def duplicate_error_func():
        raise DuplicateError("Resource already exists")
    
    with pytest.raises(HTTPException) as exc_info:
        await duplicate_error_func()
    
    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert exc_info.value.detail == "Resource already exists"


@pytest.mark.asyncio
async def test_handle_service_errors_business_rule_violation():
    """Should convert BusinessRuleViolation to 422 HTTPException."""
    
    @handle_service_errors
    async def business_rule_func():
        raise BusinessRuleViolation("Business rule failed")
    
    with pytest.raises(HTTPException) as exc_info:
        await business_rule_func()
    
    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert exc_info.value.detail == "Business rule failed"


@pytest.mark.asyncio
async def test_handle_service_errors_unexpected_exception():
    """Should convert unexpected exceptions to 500 HTTPException."""
    
    @handle_service_errors
    async def unexpected_error_func():
        raise RuntimeError("Something went wrong")
    
    with pytest.raises(HTTPException) as exc_info:
        await unexpected_error_func()
    
    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "An unexpected error occurred" in exc_info.value.detail
    assert "Something went wrong" in exc_info.value.detail


@pytest.mark.asyncio
async def test_handle_service_errors_with_args_and_kwargs():
    """Should pass through args and kwargs to wrapped function."""
    
    @handle_service_errors
    async def func_with_params(a, b, c=None):
        return {"a": a, "b": b, "c": c}
    
    result = await func_with_params(1, 2, c=3)
    assert result == {"a": 1, "b": 2, "c": 3}


# ==================== Tests for register_error_handlers ====================


@pytest.mark.asyncio
async def test_register_fermentation_not_found_handler():
    """Should register handler for FermentationNotFound returning 404."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    # Verify handler was registered
    assert FermentationNotFound in handlers
    
    # Test the handler
    handler = handlers[FermentationNotFound]
    request = Mock(spec=Request)
    exc = FermentationNotFound(message="Fermentation not found", fermentation_id=123)
    
    response = await handler(request, exc)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # Check the content dict directly
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "FermentationNotFound"


@pytest.mark.asyncio
async def test_register_sample_not_found_handler():
    """Should register handler for SampleNotFound returning 404."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    assert SampleNotFound in handlers
    
    handler = handlers[SampleNotFound]
    request = Mock(spec=Request)
    exc = SampleNotFound(message="Sample not found", sample_id=456)
    
    response = await handler(request, exc)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "SampleNotFound"


@pytest.mark.asyncio
async def test_register_invalid_fermentation_state_handler():
    """Should register handler for InvalidFermentationState returning 422."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    assert InvalidFermentationState in handlers
    
    handler = handlers[InvalidFermentationState]
    request = Mock(spec=Request)
    exc = InvalidFermentationState(
        message="Cannot modify completed fermentation",
        fermentation_id=123,
        current_state="completed"
    )
    
    response = await handler(request, exc)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "InvalidFermentationState"


@pytest.mark.asyncio
async def test_register_fermentation_already_completed_handler():
    """Should register handler for FermentationAlreadyCompleted returning 409."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    assert FermentationAlreadyCompleted in handlers
    
    handler = handlers[FermentationAlreadyCompleted]
    request = Mock(spec=Request)
    exc = FermentationAlreadyCompleted(message="Fermentation already completed", fermentation_id=123)
    
    response = await handler(request, exc)
    
    assert response.status_code == status.HTTP_409_CONFLICT
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "FermentationAlreadyCompleted"


@pytest.mark.asyncio
async def test_register_invalid_sample_date_handler():
    """Should register handler for InvalidSampleDate returning 422."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    assert InvalidSampleDate in handlers
    
    handler = handlers[InvalidSampleDate]
    request = Mock(spec=Request)
    exc = InvalidSampleDate(message="Date is in the future", sample_date="2026-01-01")
    
    response = await handler(request, exc)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "InvalidSampleDate"


@pytest.mark.asyncio
async def test_register_invalid_sample_value_handler():
    """Should register handler for InvalidSampleValue returning 422."""
    mock_app = Mock()
    handlers = {}
    
    def exception_handler(exc_class):
        def decorator(func):
            handlers[exc_class] = func
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    assert InvalidSampleValue in handlers
    
    handler = handlers[InvalidSampleValue]
    request = Mock(spec=Request)
    exc = InvalidSampleValue(
        message="Brix cannot be negative",
        sample_id=789,
        field="brix",
        value=-5.0
    )
    
    response = await handler(request, exc)
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    import json
    body_dict = json.loads(response.body)
    assert body_dict["error_type"] == "InvalidSampleValue"


@pytest.mark.asyncio
async def test_register_all_handlers_at_once():
    """Should register all 6 domain error handlers."""
    mock_app = Mock()
    registered_handlers = []
    
    def exception_handler(exc_class):
        def decorator(func):
            registered_handlers.append(exc_class)
            return func
        return decorator
    
    mock_app.exception_handler = exception_handler
    
    register_error_handlers(mock_app)
    
    # Verify all 6 domain error handlers were registered
    expected_handlers = [
        FermentationNotFound,
        SampleNotFound,
        InvalidFermentationState,
        FermentationAlreadyCompleted,
        InvalidSampleDate,
        InvalidSampleValue
    ]
    
    for exc_class in expected_handlers:
        assert exc_class in registered_handlers, f"{exc_class.__name__} handler not registered"

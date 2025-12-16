"""
Pytest Fixtures for Unit Testing

Provides reusable fixtures for common test dependencies.
"""

from .validation_result_factory import (
    ValidationError,
    ValidationResult,
    ValidationResultFactory,
    create_valid_result,
    create_invalid_result,
    create_single_error_result,
    create_field_errors_result,
    create_multiple_errors_result,
)

__all__ = [
    "ValidationError",
    "ValidationResult",
    "ValidationResultFactory",
    "create_valid_result",
    "create_invalid_result",
    "create_single_error_result",
    "create_field_errors_result",
    "create_multiple_errors_result",
]

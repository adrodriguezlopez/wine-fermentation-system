"""
Shared Unit Testing Infrastructure

Provides reusable utilities for creating unit tests with consistent patterns.
Implements ADR-012: Unit Test Infrastructure Refactoring.

Main Components:
- mocks: Mock builders for common dependencies (SessionManager, Repositories, etc.)
- fixtures: Reusable pytest fixtures
- builders: Entity and DTO builders for test data
"""

from .mocks.session_manager_builder import (
    create_mock_session_manager,
    MockSessionManagerBuilder,
)
from .builders.query_result_builder import (
    QueryResultBuilder,
    create_query_result,
    create_scalar_result,
    create_empty_result,
)
from .builders.entity_factory import (
    EntityFactory,
    EntityDefaults,
    create_mock_entity,
    create_mock_entities,
)
from .fixtures.validation_result_factory import (
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
    # Session Manager Mocks
    "create_mock_session_manager",
    "MockSessionManagerBuilder",
    # Query Result Builders
    "QueryResultBuilder",
    "create_query_result",
    "create_scalar_result",
    "create_empty_result",
    # Entity Factory
    "EntityFactory",
    "EntityDefaults",
    "create_mock_entity",
    "create_mock_entities",
    # Validation Result Factory
    "ValidationError",
    "ValidationResult",
    "ValidationResultFactory",
    "create_valid_result",
    "create_invalid_result",
    "create_single_error_result",
    "create_field_errors_result",
    "create_multiple_errors_result",
]

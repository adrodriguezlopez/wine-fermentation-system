"""
Data Builders for Unit Testing

Provides builders for creating test entities and DTOs with realistic data.
"""

from .query_result_builder import (
    QueryResultBuilder,
    create_query_result,
    create_scalar_result,
    create_empty_result,
)
from .entity_factory import (
    EntityFactory,
    EntityDefaults,
    create_mock_entity,
    create_mock_entities,
)

__all__ = [
    "QueryResultBuilder",
    "create_query_result",
    "create_scalar_result",
    "create_empty_result",
    "EntityFactory",
    "EntityDefaults",
    "create_mock_entity",
    "create_mock_entities",
]

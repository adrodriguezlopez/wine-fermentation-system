"""
QueryResultBuilder - Creates mock SQLAlchemy query results

Provides a fluent API for creating mock Result objects that simulate
SQLAlchemy query results for testing repositories and services.

Usage:
    # Single entity result
    result = QueryResultBuilder().with_entities([entity]).build()
    
    # Empty result
    result = QueryResultBuilder().build_empty()
    
    # Scalar result
    result = QueryResultBuilder().with_scalar(entity).build_scalar()
"""

from typing import Any, List, Optional
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncResult


class QueryResultBuilder:
    """
    Builder for creating mock SQLAlchemy Result objects.
    
    Simulates the behavior of AsyncResult returned by session.execute()
    with methods like scalars(), scalar_one_or_none(), fetchall(), etc.
    """
    
    def __init__(self):
        """Initialize the builder with default empty result."""
        self._entities: List[Any] = []
        self._scalar_value: Optional[Any] = None
        self._unique_enabled = False
    
    def with_entities(self, entities: List[Any]) -> "QueryResultBuilder":
        """
        Configure the entities returned by the result.
        
        Args:
            entities: List of entities to return from fetchall(), scalars(), etc.
            
        Returns:
            Self for method chaining
        """
        self._entities = entities if entities is not None else []
        return self
    
    def with_single_entity(self, entity: Any) -> "QueryResultBuilder":
        """
        Configure a single entity result.
        
        Args:
            entity: Single entity to return
            
        Returns:
            Self for method chaining
        """
        self._entities = [entity] if entity is not None else []
        return self
    
    def with_scalar(self, value: Any) -> "QueryResultBuilder":
        """
        Configure the scalar value returned by scalar() or scalar_one_or_none().
        
        Args:
            value: The scalar value to return
            
        Returns:
            Self for method chaining
        """
        self._scalar_value = value
        return self
    
    def with_unique(self) -> "QueryResultBuilder":
        """
        Enable unique() behavior (for testing with unique() calls).
        
        Returns:
            Self for method chaining
        """
        self._unique_enabled = True
        return self
    
    def build(self) -> MagicMock:
        """
        Build a mock Result object with configured entities.
        
        Returns:
            Mock Result that can be used with scalars(), fetchall(), etc.
        """
        result = MagicMock()  # Don't use spec=AsyncResult to avoid async methods
        
        # Configure scalars() method
        scalars_result = MagicMock()
        scalars_result.all.return_value = self._entities
        scalars_result.first.return_value = self._entities[0] if self._entities else None
        scalars_result.one_or_none.return_value = self._entities[0] if len(self._entities) == 1 else None
        scalars_result.one.return_value = self._entities[0] if len(self._entities) == 1 else None
        scalars_result.unique.return_value = scalars_result  # For chaining unique().all()
        
        result.scalars.return_value = scalars_result
        
        # Configure scalar methods
        result.scalar_one_or_none.return_value = self._scalar_value if self._scalar_value is not None else (
            self._entities[0] if len(self._entities) == 1 else None
        )
        result.scalar.return_value = self._scalar_value if self._scalar_value is not None else (
            self._entities[0] if self._entities else None
        )
        result.scalar_one.return_value = self._scalar_value if self._scalar_value is not None else (
            self._entities[0] if len(self._entities) == 1 else None
        )
        
        # Configure fetchall and other methods
        result.fetchall.return_value = [(entity,) for entity in self._entities]
        result.fetchone.return_value = (self._entities[0],) if self._entities else None
        result.first.return_value = (self._entities[0],) if self._entities else None
        result.all.return_value = [(entity,) for entity in self._entities]
        result.one_or_none.return_value = (self._entities[0],) if len(self._entities) == 1 else None
        result.one.return_value = (self._entities[0],) if len(self._entities) == 1 else None
        
        # Configure unique() method
        result.unique.return_value = result  # Returns self for chaining
        
        return result
    
    def build_empty(self) -> MagicMock:
        """
        Build a mock Result representing an empty query result.
        
        Returns:
            Mock Result with no entities
        """
        return self.with_entities([]).build()
    
    def build_scalar(self) -> MagicMock:
        """
        Build a mock Result optimized for scalar queries.
        
        Returns:
            Mock Result for scalar value queries
        """
        result = MagicMock()  # Don't use spec to avoid async methods
        
        result.scalar_one_or_none.return_value = self._scalar_value
        result.scalar.return_value = self._scalar_value
        result.scalar_one.return_value = self._scalar_value
        
        return result


def create_query_result(entities: Optional[List[Any]] = None) -> MagicMock:
    """
    Factory function for creating a simple query result.
    
    Args:
        entities: Optional list of entities to return
        
    Returns:
        Mock Result object
        
    Examples:
        # Empty result
        result = create_query_result()
        
        # Single entity
        result = create_query_result([entity])
        
        # Multiple entities
        result = create_query_result([entity1, entity2])
        
        # For complex scenarios, use the builder
        result = (
            QueryResultBuilder()
            .with_entities([entity1, entity2])
            .with_unique()
            .build()
        )
    """
    return QueryResultBuilder().with_entities(entities or []).build()


def create_scalar_result(value: Any) -> MagicMock:
    """
    Factory function for creating a scalar query result.
    
    Args:
        value: The scalar value to return
        
    Returns:
        Mock Result for scalar queries
        
    Example:
        result = create_scalar_result(42)
        assert result.scalar_one_or_none() == 42
    """
    return QueryResultBuilder().with_scalar(value).build_scalar()


def create_empty_result() -> MagicMock:
    """
    Factory function for creating an empty query result.
    
    Returns:
        Mock Result with no entities
        
    Example:
        result = create_empty_result()
        assert result.scalars().all() == []
    """
    return QueryResultBuilder().build_empty()

"""
Tests for QueryResultBuilder

Validates the behavior and API of the query result builder.
Follows TDD principles from ADR-012.
"""

import pytest
from unittest.mock import MagicMock

from src.shared.testing.unit.builders.query_result_builder import (
    QueryResultBuilder,
    create_query_result,
    create_scalar_result,
    create_empty_result,
)


class TestQueryResultBuilder:
    """Test suite for QueryResultBuilder"""
    
    def test_build_empty_result(self):
        """Should create empty result"""
        # Act
        result = QueryResultBuilder().build_empty()
        
        # Assert
        assert result.scalars().all() == []
        assert result.scalar_one_or_none() is None
        assert result.scalar() is None
        assert result.first() is None
    
    def test_build_with_single_entity(self):
        """Should create result with single entity"""
        # Arrange
        entity = MagicMock(id=1, name="Test")
        
        # Act
        result = QueryResultBuilder().with_single_entity(entity).build()
        
        # Assert
        assert result.scalars().all() == [entity]
        assert result.scalars().first() == entity
        assert result.scalars().one_or_none() == entity
        assert result.scalar_one_or_none() == entity
        assert result.scalar() == entity
    
    def test_build_with_multiple_entities(self):
        """Should create result with multiple entities"""
        # Arrange
        entity1 = MagicMock(id=1, name="Test1")
        entity2 = MagicMock(id=2, name="Test2")
        entities = [entity1, entity2]
        
        # Act
        result = QueryResultBuilder().with_entities(entities).build()
        
        # Assert
        assert result.scalars().all() == entities
        assert result.scalars().first() == entity1
        # one_or_none() should return None for multiple entities
        assert result.scalars().one_or_none() is None
    
    def test_with_scalar_value(self):
        """Should configure scalar value"""
        # Arrange
        scalar_value = 42
        
        # Act
        result = QueryResultBuilder().with_scalar(scalar_value).build_scalar()
        
        # Assert
        assert result.scalar_one_or_none() == scalar_value
        assert result.scalar() == scalar_value
        assert result.scalar_one() == scalar_value
    
    def test_unique_chaining(self):
        """Should support unique() method chaining"""
        # Arrange
        entity1 = MagicMock(id=1)
        entity2 = MagicMock(id=2)
        entities = [entity1, entity2]
        
        # Act
        result = QueryResultBuilder().with_entities(entities).build()
        
        # Assert - unique() should return self for chaining
        unique_result = result.unique()
        assert unique_result.scalars().all() == entities
    
    def test_builder_pattern_chaining(self):
        """Should support fluent builder pattern"""
        # Arrange
        entity = MagicMock(id=1, name="Test")
        
        # Act
        result = (
            QueryResultBuilder()
            .with_single_entity(entity)
            .with_unique()
            .build()
        )
        
        # Assert
        assert result.scalars().all() == [entity]
    
    def test_scalars_all_method(self):
        """Should support scalars().all() pattern"""
        # Arrange
        entities = [MagicMock(id=i) for i in range(3)]
        
        # Act
        result = QueryResultBuilder().with_entities(entities).build()
        
        # Assert
        scalars = result.scalars()
        assert scalars.all() == entities
    
    def test_scalars_first_method(self):
        """Should support scalars().first() pattern"""
        # Arrange
        entity1 = MagicMock(id=1)
        entity2 = MagicMock(id=2)
        
        # Act
        result = QueryResultBuilder().with_entities([entity1, entity2]).build()
        
        # Assert
        assert result.scalars().first() == entity1
    
    def test_scalars_first_empty_result(self):
        """Should return None for scalars().first() on empty result"""
        # Act
        result = QueryResultBuilder().build_empty()
        
        # Assert
        assert result.scalars().first() is None
    
    def test_scalar_one_or_none_single_entity(self):
        """Should return entity for scalar_one_or_none() with single entity"""
        # Arrange
        entity = MagicMock(id=1)
        
        # Act
        result = QueryResultBuilder().with_single_entity(entity).build()
        
        # Assert
        assert result.scalar_one_or_none() == entity
    
    def test_scalar_one_or_none_empty_result(self):
        """Should return None for scalar_one_or_none() on empty result"""
        # Act
        result = QueryResultBuilder().build_empty()
        
        # Assert
        assert result.scalar_one_or_none() is None
    
    def test_fetchall_returns_tuples(self):
        """Should return tuples from fetchall() (legacy SQLAlchemy pattern)"""
        # Arrange
        entity1 = MagicMock(id=1)
        entity2 = MagicMock(id=2)
        
        # Act
        result = QueryResultBuilder().with_entities([entity1, entity2]).build()
        
        # Assert
        rows = result.fetchall()
        assert rows == [(entity1,), (entity2,)]
    
    def test_with_entities_none_creates_empty(self):
        """Should handle None entities gracefully"""
        # Act
        result = QueryResultBuilder().with_entities(None).build()
        
        # Assert
        assert result.scalars().all() == []
    
    def test_with_single_entity_none_creates_empty(self):
        """Should handle None single entity gracefully"""
        # Act
        result = QueryResultBuilder().with_single_entity(None).build()
        
        # Assert
        assert result.scalars().all() == []


class TestFactoryFunctions:
    """Test convenience factory functions"""
    
    def test_create_query_result_empty(self):
        """Should create empty result by default"""
        # Act
        result = create_query_result()
        
        # Assert
        assert result.scalars().all() == []
    
    def test_create_query_result_with_entities(self):
        """Should create result with entities"""
        # Arrange
        entities = [MagicMock(id=i) for i in range(3)]
        
        # Act
        result = create_query_result(entities)
        
        # Assert
        assert result.scalars().all() == entities
    
    def test_create_scalar_result(self):
        """Should create scalar result"""
        # Arrange
        value = 42
        
        # Act
        result = create_scalar_result(value)
        
        # Assert
        assert result.scalar_one_or_none() == value
        assert result.scalar() == value
    
    def test_create_empty_result(self):
        """Should create empty result"""
        # Act
        result = create_empty_result()
        
        # Assert
        assert result.scalars().all() == []
        assert result.scalar_one_or_none() is None


class TestSQLAlchemyPatterns:
    """Test common SQLAlchemy query patterns"""
    
    def test_select_all_pattern(self):
        """Should support SELECT * pattern"""
        # Arrange
        entities = [MagicMock(id=i) for i in range(5)]
        result = create_query_result(entities)
        
        # Act - Simulate: (await session.execute(select(Model))).scalars().all()
        all_entities = result.scalars().all()
        
        # Assert
        assert all_entities == entities
    
    def test_select_one_or_none_pattern(self):
        """Should support SELECT one_or_none pattern"""
        # Arrange
        entity = MagicMock(id=1)
        result = create_query_result([entity])
        
        # Act - Simulate: (await session.execute(select(Model).where(...))).scalars().one_or_none()
        found = result.scalars().one_or_none()
        
        # Assert
        assert found == entity
    
    def test_select_unique_all_pattern(self):
        """Should support unique().scalars().all() pattern"""
        # Arrange
        entities = [MagicMock(id=i) for i in range(3)]
        result = create_query_result(entities)
        
        # Act - Simulate: (await session.execute(select(Model))).unique().scalars().all()
        unique_entities = result.unique().scalars().all()
        
        # Assert
        assert unique_entities == entities
    
    def test_count_pattern(self):
        """Should support COUNT query pattern"""
        # Arrange
        count = 42
        result = create_scalar_result(count)
        
        # Act - Simulate: (await session.execute(select(func.count()))).scalar()
        total = result.scalar()
        
        # Assert
        assert total == count
    
    def test_exists_pattern(self):
        """Should support EXISTS query pattern"""
        # Arrange
        result_exists = create_scalar_result(True)
        result_not_exists = create_scalar_result(False)
        
        # Act
        exists = result_exists.scalar()
        not_exists = result_not_exists.scalar()
        
        # Assert
        assert exists is True
        assert not_exists is False

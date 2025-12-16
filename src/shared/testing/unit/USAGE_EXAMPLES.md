# ADR-012 Unit Testing Infrastructure - Usage Examples

## Overview

This document provides practical examples of using the shared unit testing infrastructure implemented in ADR-012.

## MockSessionManagerBuilder

### Basic Usage

```python
from src.shared.testing.unit import create_mock_session_manager

@pytest.fixture
def mock_session_manager():
    return create_mock_session_manager()

@pytest.mark.asyncio
async def test_repository_get_by_id(mock_session_manager):
    # Arrange
    entity = Fermentation(id=UUID("..."), name="Test")
    mock_result = create_query_result([entity])
    
    mock_session_manager = create_mock_session_manager(
        execute_result=mock_result
    )
    
    repository = FermentationRepository(mock_session_manager)
    
    # Act
    result = await repository.get_by_id(entity.id)
    
    # Assert
    assert result == entity
```

### Advanced Usage with Builder Pattern

```python
from src.shared.testing.unit import MockSessionManagerBuilder

@pytest.mark.asyncio
async def test_repository_handles_commit_failure():
    # Arrange
    mock_sm = (
        MockSessionManagerBuilder()
        .with_execute_result(mock_result)
        .with_commit_side_effect(Exception("Commit failed"))
        .build()
    )
    
    repository = FermentationRepository(mock_sm)
    
    # Act & Assert
    with pytest.raises(Exception, match="Commit failed"):
        await repository.save(entity)
```

## QueryResultBuilder

### Basic Usage - Multiple Entities

```python
from src.shared.testing.unit import create_query_result

@pytest.mark.asyncio
async def test_repository_get_all():
    # Arrange
    entities = [
        Fermentation(id=UUID("..."), name="Test1"),
        Fermentation(id=UUID("..."), name="Test2"),
    ]
    
    mock_result = create_query_result(entities)
    mock_sm = create_mock_session_manager(execute_result=mock_result)
    
    repository = FermentationRepository(mock_sm)
    
    # Act
    results = await repository.get_all()
    
    # Assert
    assert len(results) == 2
    assert results == entities
```

### Single Entity Result

```python
from src.shared.testing.unit import create_query_result

@pytest.mark.asyncio
async def test_repository_get_one():
    # Arrange
    entity = Fermentation(id=UUID("..."), name="Test")
    mock_result = create_query_result([entity])
    
    # The result will correctly return:
    # - result.scalars().all() -> [entity]
    # - result.scalars().one_or_none() -> entity
    # - result.scalar_one_or_none() -> entity
```

### Empty Result

```python
from src.shared.testing.unit import create_empty_result

@pytest.mark.asyncio
async def test_repository_not_found():
    # Arrange
    mock_result = create_empty_result()
    mock_sm = create_mock_session_manager(execute_result=mock_result)
    
    repository = FermentationRepository(mock_sm)
    
    # Act
    result = await repository.get_by_id(UUID("..."))
    
    # Assert
    assert result is None
```

### Scalar Results (COUNT, EXISTS, etc.)

```python
from src.shared.testing.unit import create_scalar_result

@pytest.mark.asyncio
async def test_repository_count():
    # Arrange
    count = 42
    mock_result = create_scalar_result(count)
    mock_sm = create_mock_session_manager(execute_result=mock_result)
    
    repository = FermentationRepository(mock_sm)
    
    # Act
    total = await repository.count()
    
    # Assert
    assert total == count
```

### Complex Builder Pattern

```python
from src.shared.testing.unit import QueryResultBuilder

def test_complex_query_result():
    # Arrange
    entities = [...]
    
    result = (
        QueryResultBuilder()
        .with_entities(entities)
        .with_unique()  # For unique().scalars().all() pattern
        .build()
    )
    
    # Use result
    assert result.unique().scalars().all() == entities
```

## Complete Repository Test Example

```python
import pytest
from uuid import UUID
from unittest.mock import MagicMock

from src.shared.testing.unit import (
    create_mock_session_manager,
    create_query_result,
    create_empty_result,
    create_scalar_result,
    MockSessionManagerBuilder,
)
from src.modules.fermentation.domain.entities import Fermentation
from src.modules.fermentation.infrastructure.repositories import FermentationRepository


class TestFermentationRepository:
    
    @pytest.mark.asyncio
    async def test_get_by_id_found(self):
        # Arrange
        fermentation_id = UUID("12345678-1234-1234-1234-123456789012")
        fermentation = Fermentation(id=fermentation_id, name="Test")
        
        mock_result = create_query_result([fermentation])
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        repository = FermentationRepository(mock_sm)
        
        # Act
        result = await repository.get_by_id(fermentation_id)
        
        # Assert
        assert result == fermentation
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        # Arrange
        fermentation_id = UUID("12345678-1234-1234-1234-123456789012")
        
        mock_result = create_empty_result()
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        repository = FermentationRepository(mock_sm)
        
        # Act
        result = await repository.get_by_id(fermentation_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_all(self):
        # Arrange
        fermentations = [
            Fermentation(id=UUID("..."), name="Test1"),
            Fermentation(id=UUID("..."), name="Test2"),
        ]
        
        mock_result = create_query_result(fermentations)
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        repository = FermentationRepository(mock_sm)
        
        # Act
        results = await repository.get_all()
        
        # Assert
        assert len(results) == 2
        assert results == fermentations
    
    @pytest.mark.asyncio
    async def test_save_commit_failure(self):
        # Arrange
        fermentation = Fermentation(id=UUID("..."), name="Test")
        
        mock_sm = (
            MockSessionManagerBuilder()
            .with_commit_side_effect(Exception("Database error"))
            .build()
        )
        
        repository = FermentationRepository(mock_sm)
        
        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await repository.save(fermentation)
    
    @pytest.mark.asyncio
    async def test_count(self):
        # Arrange
        count = 15
        mock_result = create_scalar_result(count)
        mock_sm = create_mock_session_manager(execute_result=mock_result)
        
        repository = FermentationRepository(mock_sm)
        
        # Act
        total = await repository.count()
        
        # Assert
        assert total == count
```

## Migration from Old Pattern

### Before (ADR-012)

```python
@pytest.fixture
def mock_session_manager():
    # 20 lines of boilerplate code
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.refresh = AsyncMock()
    
    mock_session_manager = AsyncMock(spec=ISessionManager)
    
    @asynccontextmanager
    async def mock_get_session():
        yield mock_session
    
    mock_session_manager.get_session = mock_get_session
    mock_session_manager.close = AsyncMock()
    
    return mock_session_manager

@pytest.fixture
def mock_result():
    # 15 lines of boilerplate code
    result = AsyncMock(spec=AsyncResult)
    scalars_result = MagicMock()
    scalars_result.all.return_value = []
    # ... more setup
    return result
```

### After (ADR-012)

```python
# 1 line!
from src.shared.testing.unit import create_mock_session_manager, create_query_result

@pytest.fixture
def mock_session_manager():
    return create_mock_session_manager()

@pytest.fixture
def mock_result():
    return create_query_result([])
```

**Result: From ~35 lines to 2 lines = 94% reduction in boilerplate!**

## Benefits Summary

1. ✅ **Consistency**: All tests use the same mock patterns
2. ✅ **Simplicity**: Factory functions for common cases
3. ✅ **Flexibility**: Builder pattern for complex scenarios
4. ✅ **Type Safety**: Full typing support
5. ✅ **Maintainability**: Changes to infrastructure affect all tests automatically
6. ✅ **Readability**: Clear, self-documenting test code
7. ✅ **Speed**: 50% faster test creation (per ADR-012 goals)

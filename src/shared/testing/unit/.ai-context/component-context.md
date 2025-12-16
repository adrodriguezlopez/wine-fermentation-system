# Component Context: Unit Testing Infrastructure

> **Parent Context**: See `../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`
> **ADR Reference**: ADR-012 (Unit Test Infrastructure Refactoring)

## Component responsibility
Provides reusable mock utilities, builders, and fixtures for writing unit tests across the wine fermentation system. Eliminates 750-1,100 lines of duplicated test code by centralizing common mocking patterns for SessionManager, SQLAlchemy results, entities, and validation results.

**Position in module**: Core component of the testing infrastructure. Used by all repository and service unit tests across Fermentation, Fruit Origin, Winery, and Auth modules.

## Architecture pattern
- **Builder Pattern**: Fluent API for configuring complex mock objects
- **Factory Pattern**: Centralized entity and result creation
- **Fixture Pattern**: pytest fixtures for reusable components
- **Convenience Functions**: Simple wrappers for common scenarios

## Component structure

```
unit/
├── __init__.py                          # Public API exports
├── README.md                             # Architecture documentation
├── USAGE_EXAMPLES.md                     # Practical usage guide
├── mocks/
│   ├── __init__.py                      # Mock utilities exports
│   └── session_manager_builder.py      # MockSessionManagerBuilder
├── builders/
│   ├── __init__.py                      # Builder utilities exports
│   ├── query_result_builder.py         # QueryResultBuilder
│   └── entity_factory.py                # EntityFactory
├── fixtures/
│   ├── __init__.py                      # Fixture utilities exports
│   └── validation_result_factory.py    # ValidationResultFactory
└── tests/
    ├── test_session_manager_builder.py  # 14 tests
    ├── test_query_result_builder.py     # 23 tests
    ├── test_entity_factory.py           # 23 tests
    └── test_validation_result_factory.py # 26 tests
```

## Core Components

### 1. MockSessionManagerBuilder (mocks/session_manager_builder.py)

**Purpose**: Create mock ISessionManager instances with configurable behavior

**Features**:
- Fluent API with method chaining
- Pre-configured AsyncMock session
- Execute result configuration
- Side effects for flush, commit, rollback, close
- Async context manager support

**API**:
```python
class MockSessionManagerBuilder:
    def with_execute_result(result) -> Self
    def with_execute_side_effect(effect) -> Self
    def with_commit_side_effect(effect) -> Self
    def with_rollback_side_effect(effect) -> Self
    def with_flush_side_effect(effect) -> Self  # Added Phase 3
    def with_close_side_effect(effect) -> Self
    def with_session(session) -> Self
    def build() -> ISessionManager

# Convenience function
def create_mock_session_manager(...) -> ISessionManager
```

**Usage**:
```python
session_manager = (
    MockSessionManagerBuilder()
    .with_execute_result(mock_result)
    .with_flush_side_effect(IntegrityError(...))
    .build()
)
```

**Tests**: 14 comprehensive tests covering all methods and scenarios

---

### 2. QueryResultBuilder (builders/query_result_builder.py)

**Purpose**: Create mock SQLAlchemy Result objects for query mocking

**Features**:
- Support for all query patterns (scalar, first, all, scalars)
- Single entity or list configuration
- Empty result support
- Chainable scalar methods

**API**:
```python
class QueryResultBuilder:
    def with_scalar_result(entity) -> Self
    def with_single_result(entity) -> Self
    def with_list_result(entities) -> Self
    def build() -> Result

# Convenience functions
def create_query_result(entities: List) -> Result
def create_empty_result() -> Result
```

**Usage**:
```python
# Single entity
result = create_query_result([entity])
# or
result = QueryResultBuilder().with_single_result(entity).build()

# Empty result
result = create_empty_result()
```

**Tests**: 23 comprehensive tests covering all query patterns

---

### 3. EntityFactory (builders/entity_factory.py)

**Purpose**: Create mock entities with sensible defaults

**Features**:
- Registry-based default values
- Override defaults with kwargs
- Batch entity creation
- Support for all entity types

**API**:
```python
class EntityFactory:
    @staticmethod
    def register_defaults(entity_class, **defaults)
    
    @staticmethod
    def create(entity_class, **overrides) -> Mock
    
    @staticmethod
    def create_batch(entity_class, count, **common_overrides) -> List[Mock]

# Convenience function
def create_mock_entity(entity_class, **kwargs) -> Mock
```

**Default Registry**:
- User: id, username, email, full_name, winery_id, role, is_active, etc.
- Fermentation: id, winery_id, vintage_year, vessel_code, status, etc.
- Sample: id, fermentation_id, sample_type_code, timestamp, etc.
- HarvestLot, Vineyard, VineyardBlock: Domain-specific defaults

**Usage**:
```python
# With defaults
user = create_mock_entity(User)

# With overrides
user = create_mock_entity(User, id=99, username="custom")

# Batch creation
users = EntityFactory.create_batch(User, count=5, winery_id=100)
```

**Tests**: 23 comprehensive tests covering all entity types

---

### 4. ValidationResultFactory (fixtures/validation_result_factory.py)

**Purpose**: Create validation result objects for testing validation logic

**Features**:
- Dataclass-based results
- Success and error builders
- Helper methods for common scenarios
- Supports errors, warnings, info messages

**API**:
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def add_error(message: str) -> Self
    def add_warning(message: str) -> Self
    def add_info(message: str) -> Self
    
    @staticmethod
    def success() -> ValidationResult
    
    @staticmethod
    def failure(errors: List[str]) -> ValidationResult

# Convenience function
def create_validation_result(is_valid=True, **kwargs) -> ValidationResult
```

**Usage**:
```python
# Success
result = ValidationResult.success()

# Failure with errors
result = ValidationResult.failure(["Error 1", "Error 2"])

# With warnings
result = create_validation_result(
    is_valid=True,
    warnings=["Warning message"]
)
```

**Tests**: 26 comprehensive tests covering all scenarios

---

## Migration Pattern (ADR-012)

### Standard Repository Test Pattern

```python
"""
Repository tests using ADR-012 shared infrastructure.
"""
import pytest
from src.shared.testing.unit import (
    MockSessionManagerBuilder,
    create_query_result,
    create_empty_result,
    create_mock_entity,
)

# Fixtures - create entities with defaults
@pytest.fixture
def sample_entity():
    return create_mock_entity(
        EntityClass,
        id=1,
        name="Test",
        is_deleted=False
    )

# Tests - create session manager and repository inline
class TestRepository:
    @pytest.mark.asyncio
    async def test_get_by_id_found(self, sample_entity):
        # Arrange
        result = create_query_result([sample_entity])
        
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = SomeRepository(session_manager)
        
        # Act
        actual = await repository.get_by_id(1, 100)
        
        # Assert
        assert actual == sample_entity
    
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self):
        # Arrange
        result = create_empty_result()
        
        session_manager = (
            MockSessionManagerBuilder()
            .with_execute_result(result)
            .build()
        )
        repository = SomeRepository(session_manager)
        
        # Act
        actual = await repository.get_by_id(999, 100)
        
        # Assert
        assert actual is None
```

### Error Handling Pattern

```python
@pytest.mark.asyncio
async def test_create_duplicate_raises_error(self, sample_entity):
    # Arrange
    from sqlalchemy.exc import IntegrityError
    
    result = create_query_result([sample_entity])
    
    error = IntegrityError("...", "...", "...", connection_invalidated=False)
    error.args = ("duplicate key violates unique constraint",)
    
    session_manager = (
        MockSessionManagerBuilder()
        .with_execute_result(result)
        .with_flush_side_effect(error)  # Error on flush
        .build()
    )
    repository = SomeRepository(session_manager)
    
    # Act & Assert
    with pytest.raises(DuplicateCodeError):
        await repository.create(...)
```

## Component interfaces

### Public API (Exported from `__init__.py`)

```python
from .mocks import (
    MockSessionManagerBuilder,
    create_mock_session_manager,
)

from .builders import (
    QueryResultBuilder,
    create_query_result,
    create_empty_result,
    EntityFactory,
    create_mock_entity,
)

from .fixtures import (
    ValidationResult,
    ValidationResultFactory,
    create_validation_result,
)
```

## Business rules enforced

### Test Isolation
- Each test creates its own session manager and repository
- No shared state between tests
- Fixtures provide entity templates, not shared instances

### Pattern Consistency
- All repository tests follow identical structure
- Same imports across all test files
- Predictable test organization

### Encapsulation
- Never access repository internal attributes (e.g., `repository._session_manager`)
- Configure session manager before repository creation
- Repository is a black box in tests

### Error Handling
- Use side effects to simulate errors
- Test all error paths (flush, commit, execute)
- Verify proper exception translation

## Implementation status

**Status:** ✅ **PRODUCTION READY** | 🎯 **86/86 Tests Passing**  
**Last Updated:** December 15, 2025

### Test Coverage
- MockSessionManagerBuilder: 14 tests ✅
- QueryResultBuilder: 23 tests ✅
- EntityFactory: 23 tests ✅
- ValidationResultFactory: 26 tests ✅
- **Total**: 86 tests (100% passing)

### Migration Progress (Phase 3 Complete)
- **Phase 2**: Fermentation module - 4 files, 50 tests ✅
- **Phase 3**: Fruit Origin module - 3 files, 71 tests ✅
- **Phase 3**: Winery module - 1 file, 22 tests ✅
- **Total**: 8 files, 142+ tests migrated, ~800-1,000 lines eliminated

### Code Reduction
- ~50% fixture code reduction per file
- ~80-100 lines eliminated per file
- ~800-1,000 total lines removed

## Performance characteristics
- **Test execution**: All 86 tests in <1 second
- **Mock creation**: Instantaneous (pure Python)
- **No I/O**: All operations in-memory
- **Fast feedback**: Sub-second test suite

## Known limitations
- **UserRepository**: Not migrated (uses direct session pattern)
- **Service tests**: Not yet migrated
- **Complex queries**: May need custom result configuration
- **Transaction testing**: No explicit transaction utilities yet

## Future enhancements
- [ ] Add transaction testing utilities
- [ ] Create codemod for automated migration
- [ ] Add more entity defaults based on usage
- [ ] Service test utilities (if pattern emerges)
- [ ] Performance profiling utilities

## Testing strategy
- **Self-testing**: Every utility has comprehensive tests
- **Real usage**: Validated through 8 migrated files
- **Regression prevention**: All tests must pass
- **Documentation**: README + USAGE_EXAMPLES

## Documentation
- [README.md](../README.md) - Architecture overview
- [USAGE_EXAMPLES.md](../USAGE_EXAMPLES.md) - Practical examples
- [ADR-012](../../../.ai-context/adr/ADR-012-unit-test-infrastructure-refactoring.md) - Design decisions

## Team guidelines
1. **Always use shared utilities** for new tests
2. **Never access internal repository attributes**
3. **Create session manager before repository** in each test
4. **Use convenience functions** for common scenarios
5. **Follow migration pattern** from USAGE_EXAMPLES.md
6. **Register entity defaults** for new entity types

## Success metrics (Phase 3)
- ✅ 86 infrastructure tests (100%)
- ✅ 8 files migrated successfully
- ✅ 142+ tests using shared utilities
- ✅ 737 total project tests passing
- ✅ ~50% time savings validated
- ✅ 100% pattern consistency achieved

---

**For detailed usage examples, see [USAGE_EXAMPLES.md](../USAGE_EXAMPLES.md)**

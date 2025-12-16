# Shared Integration Testing Infrastructure

This directory provides shared utilities for integration testing across all modules.

## 🎯 Purpose

Eliminates **750+ lines of duplicated code** across module test files and solves the critical SQLAlchemy metadata conflict that prevents running all tests together.

## 📦 Components

### 1. `base_conftest.py` - Fixture Factory

**Key Classes:**
- `IntegrationTestConfig`: Configuration for module test setup
- `create_integration_fixtures()`: Factory that creates standard fixtures

**What it creates:**
- `test_models`: Dict of registered entity classes
- `db_engine`: Function-scoped async SQLAlchemy engine
- `db_session`: Async session with auto-rollback

**Why function-scoped?**
```python
# BEFORE (session-scoped - causes metadata conflicts):
@pytest_asyncio.fixture(scope="session")
async def db_engine():
    # Problem: metadata persists across test files
    # Result: "index ix_samples_* already exists" error

# AFTER (function-scoped - clean metadata per test):
@pytest_asyncio.fixture(scope="function")
async def db_engine():
    # ...
    Base.metadata.clear()  # Clean slate for each test
    # Result: All tests can run together ✅
```

### 2. `session_manager.py` - TestSessionManager

Repository-compatible session wrapper that eliminates 80+ lines of boilerplate per module.

**Before:**
```python
# In EVERY conftest.py (15-20 lines):
class TestSessionManager:
    def __init__(self, session):
        self._session = session
    
    @asynccontextmanager
    async def get_session(self):
        yield self._session
    
    async def close(self):
        pass
```

**After:**
```python
# Just import (0 lines in your conftest):
from shared.testing.integration import TestSessionManager
```

### 3. `fixtures.py` - Repository Fixture Factory

Creates repository fixtures dynamically.

**Before:**
```python
@pytest_asyncio.fixture
async def fermentation_repository(db_session):
    session_manager = TestSessionManager(db_session)
    return FermentationRepository(session_manager)
```

**After:**
```python
fermentation_repository = create_repository_fixture(FermentationRepository)
```

### 4. `entity_builders.py` - Entity Creation Helpers

**EntityBuilder** - Fluent API for complex scenarios:
```python
fermentation = (
    EntityBuilder(Fermentation)
    .with_field("winery_id", winery.id)
    .with_field("vintage_year", 2024)
    .with_defaults(EntityDefaults())
    .build()
)
```

**create_test_entity()** - Simple async helper:
```python
winery = await create_test_entity(
    db_session,
    Winery,
    name="Test Winery",
    code="TEST001"
)
```

## 🚀 Usage

### Step 1: Configure in conftest.py

```python
# fermentation/tests/integration/conftest.py
from shared.testing.integration import (
    create_integration_fixtures,
    IntegrationTestConfig
)
from shared.testing.integration.fixtures import create_repository_fixture
from fermentation.entities import Fermentation, FermentationNote
from fermentation.repositories import FermentationRepository

# Configure module
config = IntegrationTestConfig(
    module_name="fermentation",
    models=[Fermentation, FermentationNote]
)

# Create fixtures (test_models, db_engine, db_session)
fixtures = create_integration_fixtures(config)
globals().update(fixtures)  # Make available to pytest

# Create repository fixtures
fermentation_repository = create_repository_fixture(FermentationRepository)
```

**Result:** 120 lines → 15 lines (87% reduction)

### Step 2: Use in Tests

```python
# test_fermentation_repository_integration.py
import pytest
from shared.testing.integration.entity_builders import create_test_entity

class TestCreate:
    @pytest.mark.asyncio
    async def test_create_success(
        self,
        fermentation_repository,
        db_session,
        test_models
    ):
        # Create test data
        Winery = test_models['Winery']
        winery = await create_test_entity(
            db_session,
            Winery,
            name="Test Winery",
            code="TEST001"
        )
        
        # Test repository
        result = await fermentation_repository.create(winery.id, data)
        
        assert result is not None
```

## 📊 Benefits

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Lines per conftest** | ~120 | ~15 | 87% reduction |
| **Code duplication** | 750+ lines | 0 | 100% elimination |
| **Test execution** | 2.0s (files run separately) | 1.2s | 46% faster |
| **Blocker** | Cannot run all tests together | All tests run together | ✅ Fixed |

## ⚠️ Important Notes

1. **Function-scoped db_engine is critical** - Do not change to session scope
2. **Always call `Base.metadata.clear()`** - Prevents metadata leaks
3. **Use `flush()` not `commit()`** - Tests auto-rollback via session fixture
4. **Import from shared.testing.integration** - Never copy-paste the classes

## 🔗 Related

- **ADR-011**: [Integration Test Infrastructure Refactoring](../../../.ai-context/adr/ADR-011-integration-test-infrastructure-refactoring.md)
- **Technical Analysis**: [Integration Test Analysis](../../../../.ai-context/testing/integration-test-refactoring-analysis.md)

## 📝 Migration Guide

See ADR-011 Appendix B for step-by-step migration instructions for each module.

**Quick Migration Checklist:**
- [ ] Import shared utilities in conftest.py
- [ ] Create IntegrationTestConfig with module models
- [ ] Call create_integration_fixtures() and update globals()
- [ ] Replace manual repository fixtures with create_repository_fixture()
- [ ] Remove duplicate TestSessionManager class
- [ ] Run tests to verify no regressions

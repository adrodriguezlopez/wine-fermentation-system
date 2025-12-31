# ADR-011 Phase 3 Resolution - Fermentation Integration Tests

**Date:** December 30, 2025  
**Status:** ✅ Complete  
**Related ADR:** [ADR-011](./ADR-011-integration-test-infrastructure-refactoring.md)

---

## Context

ADR-011 Phase 2 left **fermentation integration tests excluded** from the main test suite due to SQLAlchemy single-table inheritance metadata conflicts with Sample models. Tests had to be run separately, which was documented as acceptable but suboptimal.

**Previous State:**
- `run_all_tests.ps1` hardcoded skip for fermentation integration tests
- 48 tests had to be run manually: `cd src/modules/fermentation && pytest tests/integration/repository_component/ -v`
- 6 UnitOfWork tests consistently failing with "Can't operate on closed transaction" errors
- Total: 796 tests passing (748 in main suite + 48 manual)

**Blocking Issues:**
1. **Metadata conflicts**: Sample models caused `sqlite3.OperationalError: index already exists`
2. **UnitOfWork failures**: Session closure invalidating test fixtures
3. **Import errors**: ADR-028 Poetry module imports failing across contexts
4. **Schema mismatches**: Winery entity schema changes not reflected in fixtures

---

## Decision

Implement **4-part resolution strategy** to enable all 49 fermentation integration tests in main suite:

### 1. Isolated Sample Repository Fixtures
**Problem:** Sample models (SugarSample, DensitySample, CelsiusTemperatureSample) register SQLAlchemy indices globally on import.

**Solution:** Create separate `repository_component/conftest.py` with isolated fixtures:
```python
# src/modules/fermentation/tests/integration/repository_component/conftest.py
from shared.testing.integration.fixtures import create_repository_fixture
from fermentation.repositories import SampleRepository

# Isolated fixture - only imports Sample models when needed
sample_repository = create_repository_fixture(SampleRepository)

@pytest_asyncio.fixture
def test_models_with_samples(test_models):
    # Late import to avoid global registration
    from fermentation.entities.samples import SugarSample, DensitySample, CelsiusTemperatureSample
    test_models['SugarSample'] = SugarSample
    test_models['DensitySample'] = DensitySample
    test_models['CelsiusTemperatureSample'] = CelsiusTemperatureSample
    return test_models
```

### 2. SessionWrapper Pattern for UnitOfWork Tests
**Problem:** UnitOfWork calls `await session.close()` in `__aexit__`, invalidating the shared test session. Multiple `async with uow:` blocks fail with "closed transaction" error.

**Solution:** Session wrapper using savepoints:
```python
@pytest.fixture
def session_manager_factory(db_session):
    @asynccontextmanager
    async def get_session():
        class SessionWrapper:
            def __init__(self, real_session):
                self._real_session = real_session
                self._savepoint = None
            
            async def commit(self):
                """Commit savepoint instead of parent transaction"""
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.commit()
            
            async def rollback(self):
                """Rollback savepoint instead of parent transaction"""
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.rollback()
            
            async def close(self):
                """Close savepoint, not the parent session"""
                if self._savepoint and self._savepoint.is_active:
                    await self._savepoint.close()
            
            def __getattr__(self, name):
                """Delegate all other operations to real session"""
                return getattr(self._real_session, name)
        
        wrapper = SessionWrapper(db_session)
        wrapper._savepoint = await db_session.begin_nested()
        try:
            yield wrapper
        finally:
            if wrapper._savepoint and wrapper._savepoint.is_active:
                await wrapper._savepoint.close()
    
    return get_session
```

**Key Innovation:** 
- Intercepts `commit()`, `rollback()`, `close()` to operate on savepoints
- Parent test transaction remains open
- Multiple UoW contexts can reuse same session
- Maintains test isolation via savepoint boundaries

### 3. ADR-028 Import Path Resolution
**Problem:** Poetry modules have different import contexts (shared module internal vs workspace root vs Poetry environment).

**Solution:** Triple try/except pattern:
```python
# shared/auth/domain/errors.py
try:
    # Attempt 1: Shared module internal context (from domain.errors)
    from domain.errors import AuthError, AuthorizationError
except ModuleNotFoundError:
    try:
        # Attempt 2: Workspace root context (from shared.domain.errors)
        from shared.domain.errors import AuthError, AuthorizationError
    except ModuleNotFoundError:
        # Attempt 3: Poetry module context (from src.shared.domain.errors)
        from src.shared.domain.errors import AuthError, AuthorizationError
```

### 4. Winery Entity Schema Updates
**Problem:** ADR-016 added `code` field and changed `region` → `location`, but old test fixtures not updated.

**Solution:** Update all Winery fixtures:
```python
@pytest_asyncio.fixture
async def test_winery(test_models, db_session):
    from uuid import uuid4
    Winery = test_models['Winery']
    winery = Winery(
        code=f"TEST-{uuid4().hex[:8].upper()}",  # NEW: Unique code
        name="Test Winery",
        location="Napa Valley"  # CHANGED: region → location
    )
    db_session.add(winery)
    await db_session.flush()
    return winery
```

---

## Implementation

### Files Modified

1. **run_all_tests.ps1**
   - Removed hardcoded skip for fermentation integration tests (lines 290-306)
   - Tests now run with main suite

2. **fermentation/tests/conftest.py** (NEW)
   - Created with sys.path setup for Poetry module compatibility
   - Adds workspace root to Python path

3. **fermentation/tests/integration/conftest.py**
   - Added `uow` fixture with SessionManagerWrapper
   - Updated `test_winery` fixture with new schema

4. **fermentation/tests/integration/repository_component/conftest.py** (NEW)
   - Created with isolated `sample_repository` fixture
   - Added `test_models_with_samples` fixture for late Sample model import

5. **fermentation/tests/integration/repository_component/test_unit_of_work_integration.py**
   - Implemented `session_manager_factory` with SessionWrapper
   - Fixed `test_commit_persists_multiple_operations` to use correct SampleRepository API

6. **fermentation/tests/integration/repository_component/test_sample_repository_integration.py**
   - Updated to use `test_models_with_samples` fixture

7. **fermentation/tests/integration/repository_component/test_fermentation_repository_integration.py**
   - Fixed 2 `other_winery` fixture creations with new schema

8. **shared/auth/domain/errors.py**
   - Added triple try/except for ADR-028 import compatibility

9. **fruit_origin/repository_component/errors.py**
   - Added try/except fallback for shared.domain.errors import

---

## Results

### Test Coverage
- **Before:** 796/796 tests passing (748 main suite + 48 manual)
- **After:** 797/797 tests passing (all in main suite)
- **New test:** 1 sample_repository integration test now included

### Fermentation Integration Tests
- **FermentationNoteRepository:** 20/20 passing ✅
- **FermentationRepository:** 22/22 passing ✅
- **HarvestLotRepository:** 21/21 passing ✅ (from fruit_origin module)
- **SampleRepository:** 1/1 passing ✅
- **UnitOfWork:** 6/6 passing ✅ (previously 1/6)
- **Total:** 49/49 passing (100%)

### Performance
- **Duration:** ~61 seconds for full suite
- **No regression:** Same performance as before

### Code Quality
- **New pattern documented:** SessionWrapper for UnitOfWork testing
- **Import strategy standardized:** Triple try/except for Poetry modules
- **Test isolation improved:** Savepoint-based transaction management

---

## Technical Deep-Dive

### Why SessionWrapper Works

The db_session fixture provides a session already inside `async with session.begin():`:

```python
# shared/testing/integration/base_conftest.py
@pytest_asyncio.fixture
async def db_session(db_engine):
    async with async_session_factory() as session:
        async with session.begin():  # ← Transaction started here
            yield session
            await session.rollback()  # ← Always rolls back
```

When UnitOfWork calls `await session.rollback()` or `await session.close()`, it affects this parent transaction, breaking subsequent test operations.

**SessionWrapper solution:**
1. Creates a savepoint (nested transaction) for each UoW context
2. Intercepts `commit()` → commits savepoint (not parent)
3. Intercepts `rollback()` → rolls back savepoint (not parent)
4. Intercepts `close()` → closes savepoint (not parent session)
5. Parent transaction remains active for next test operation

### Why Triple Try/Except Works

Poetry modules can be invoked from 3 different contexts:

1. **Internal to shared module:** `poetry run pytest` from `src/shared/`
   - Import: `from domain.errors import ...`
   
2. **Workspace root:** `poetry run pytest` from `src/modules/fermentation/`
   - Import: `from shared.domain.errors import ...`
   
3. **Poetry environment:** Module installed as package
   - Import: `from src.shared.domain.errors import ...`

Triple try/except handles all 3 contexts gracefully.

---

## Lessons Learned

1. **Savepoint pattern essential for UnitOfWork testing**
   - Cannot use simple session mocking
   - Must intercept transactional operations at method level
   - `__getattr__` magic method perfect for selective interception

2. **Late imports solve metadata conflicts**
   - Import Sample models only in tests that need them
   - Use separate conftest.py for isolated fixtures
   - Avoids global SQLAlchemy registry pollution

3. **Poetry module imports need multi-context support**
   - Cannot assume single import path
   - Triple try/except more maintainable than complex sys.path manipulation
   - Each context should work independently

4. **Schema evolution requires fixture updates**
   - Entity changes ripple through test fixtures
   - Centralized fixture creation would help (future improvement)
   - UUID-based unique codes prevent conflicts

---

## Future Improvements

1. **EntityFactory for shared fixtures**
   - Create centralized factory for Winery, User, etc.
   - Eliminates duplication across conftest.py files
   - Single source of truth for entity creation

2. **SessionWrapper as shared utility**
   - Extract to `shared/testing/integration/session_wrapper.py`
   - Document pattern for other modules with similar needs
   - Potential use case: Testing other transaction-aware patterns

3. **Import path helper utility**
   - Create `resolve_import()` helper for common triple try/except pattern
   - Reduce boilerplate across files
   - Centralized import strategy

4. **Automated schema validation**
   - Test to verify all fixtures match current entity schemas
   - Prevent schema drift issues
   - Run on CI to catch regressions early

---

## References

- [ADR-011: Integration Test Infrastructure Refactoring](./ADR-011-integration-test-infrastructure-refactoring.md)
- [ADR-028: Module Dependency Management](./ADR-028-module-dependency-management.md)
- [ADR-016: Winery Service Layer](./ADR-016-winery-service-layer.md)
- [Shared Testing Integration README](../../src/shared/testing/integration/README.md)
- [SQLAlchemy: Nested Transactions](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#using-savepoint)
- [Pytest: Fixture Scopes](https://docs.pytest.org/en/stable/how-to/fixtures.html)

---

## Status

✅ **COMPLETE** - December 30, 2025

**Verification:**
- 797/797 tests passing (100%)
- All fermentation integration tests in main suite
- No regressions in other modules
- Performance maintained (~61s total)
- Documentation updated (ADR-011, ADR-INDEX, README)

**Next Actions:**
- None - implementation complete
- Pattern available for reuse in future modules

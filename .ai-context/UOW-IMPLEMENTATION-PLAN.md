# UnitOfWork Pattern - Implementation Plan & Impact Analysis

**Date**: November 15, 2025  
**Status**: 📋 PLANNING PHASE  
**Related**: ADR-002 (Repository Architecture)

---

## Executive Summary

**Goal**: Implement Unit of Work pattern to manage transactions across multiple repositories

**Status Quo**: 
- ✅ Each repository method opens its own session/transaction
- ✅ Works well for single-repository operations
- ⚠️ No formal pattern for multi-repository transactions
- ⚠️ No way to batch operations under single transaction

**Proposed**: Implement async UnitOfWork pattern per ADR-002 specification

---

## Current Transaction Management Analysis

### How It Works Today

**Repository Level** (`FermentationRepository`, `SampleRepository`):
```python
async def create(self, winery_id: int, data: FermentationCreate) -> Fermentation:
    session_cm = await self.get_session()
    async with session_cm as session:  # <-- Each method opens its own transaction
        # Create entity
        session.add(fermentation)
        # Automatic commit on context exit (no rollback)
        # Automatic rollback on exception
    return fermentation
```

**Service Level** (`FermentationService`, `SampleService`):
```python
async def create_fermentation(self, winery_id, user_id, data):
    # Validate
    validation_result = self._validator.validate_creation_data(data)
    
    # Single repository call (single transaction)
    fermentation = await self._fermentation_repo.create(winery_id, data)
    
    return fermentation
```

### What's Missing

❌ **No multi-repository coordination**:
```python
# This CANNOT be done atomically today:
async def create_fermentation_with_blend(winery_id, fermentation_data, lot_sources):
    # Step 1: Create fermentation (Transaction #1)
    fermentation = await fermentation_repo.create(winery_id, fermentation_data)
    
    # Step 2: Create lot sources (Transaction #2, #3, #4...)
    for lot_source in lot_sources:
        await lot_source_repo.create(fermentation.id, lot_source)
    
    # PROBLEM: If step 2 fails, step 1 already committed!
```

❌ **No batch operations under single transaction**:
```python
# Cannot guarantee atomicity for bulk operations
async def bulk_update_samples(sample_updates):
    for update in sample_updates:
        await sample_repo.update(update)  # Each is separate transaction
```

❌ **No complex validation requiring multiple reads before write**:
```python
# Cannot do this atomically:
async def validate_and_create(data):
    # Read 1: Check fermentation exists
    fermentation = await fermentation_repo.get_by_id(id)
    
    # Read 2: Check samples
    samples = await sample_repo.get_samples_by_fermentation_id(id)
    
    # Validate business rules...
    
    # Write: Create new sample
    # PROBLEM: Data could have changed between reads!
```

---

## Use Cases for UnitOfWork

### 1. ✅ HIGH PRIORITY: Fermentation with Blend Creation

**Scenario**: Create fermentation from multiple harvest lots (ADR-001)

**Current Problem**:
```python
# These are 4+ separate transactions:
fermentation = await fermentation_repo.create(...)  # TX1
lot_source_1 = await lot_source_repo.create(...)    # TX2
lot_source_2 = await lot_source_repo.create(...)    # TX3
lot_source_3 = await lot_source_repo.create(...)    # TX4
# If TX4 fails, TX1-3 already committed! Orphaned data!
```

**With UnitOfWork**:
```python
async with uow:
    fermentation = await uow.fermentation_repo.create(...)
    lot_source_1 = await uow.lot_source_repo.create(...)
    lot_source_2 = await uow.lot_source_repo.create(...)
    lot_source_3 = await uow.lot_source_repo.create(...)
    await uow.commit()  # All or nothing!
```

**Business Value**: ⭐⭐⭐⭐⭐ (Critical for data integrity)

---

### 2. ✅ MEDIUM PRIORITY: Complete Fermentation Workflow

**Scenario**: Complete fermentation + create final samples

**Current Problem**:
```python
# Separate transactions
await fermentation_repo.update_status(id, "COMPLETED")     # TX1
await sample_repo.create_sample(final_sugar_sample)        # TX2
await sample_repo.create_sample(final_density_sample)      # TX3
# If TX3 fails, fermentation already marked complete!
```

**With UnitOfWork**:
```python
async with uow:
    await uow.fermentation_repo.update_status(id, "COMPLETED")
    await uow.sample_repo.create_sample(final_sugar_sample)
    await uow.sample_repo.create_sample(final_density_sample)
    await uow.commit()  # All or nothing
```

**Business Value**: ⭐⭐⭐⭐ (Important for workflow consistency)

---

### 3. ✅ LOW PRIORITY: Bulk Operations

**Scenario**: Import historical data

**Current Problem**:
```python
for fermentation in historical_data:
    await fermentation_repo.create(fermentation)  # Each is TX
    # Slow + partial failure leaves inconsistent state
```

**With UnitOfWork**:
```python
async with uow:
    for fermentation in historical_data:
        await uow.fermentation_repo.create(fermentation)
    await uow.commit()  # All succeed or all rollback
```

**Business Value**: ⭐⭐ (Nice to have for admin operations)

---

## Proposed Implementation Design

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Service Layer                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │  FermentationService                               │    │
│  │  ┌──────────────────────────────────────────┐     │    │
│  │  │  async with uow:                         │     │    │
│  │  │    fermentation = await uow.fermentation_│     │    │
│  │  │                   repo.create(...)       │     │    │
│  │  │    lot_source = await uow.lot_source_    │     │    │
│  │  │                   repo.create(...)       │     │    │
│  │  │    await uow.commit()                    │     │    │
│  │  └──────────────────────────────────────────┘     │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Repository Component                         │
│  ┌──────────────────────────────────────────────────┐       │
│  │           UnitOfWork (Coordinator)               │       │
│  │  ┌──────────────────────────────────────────┐   │       │
│  │  │  session: AsyncSession                   │   │       │
│  │  │  fermentation_repo: FermentationRepo     │   │       │
│  │  │  sample_repo: SampleRepository           │   │       │
│  │  │  lot_source_repo: LotSourceRepository    │   │       │
│  │  │                                           │   │       │
│  │  │  async __aenter__(): open session        │   │       │
│  │  │  async commit(): commit transaction      │   │       │
│  │  │  async rollback(): rollback              │   │       │
│  │  │  async __aexit__(): auto rollback/close  │   │       │
│  │  └──────────────────────────────────────────┘   │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Core Components

#### 1. `IUnitOfWork` Interface

```python
# src/modules/fermentation/src/domain/interfaces/unit_of_work_interface.py

from abc import ABC, abstractmethod
from typing import Protocol

class IUnitOfWork(Protocol):
    """
    Unit of Work pattern for managing transactional boundaries.
    
    Provides coordinated access to multiple repositories within
    a single database transaction.
    """
    
    # Repository accessors
    @property
    @abstractmethod
    def fermentation_repo(self) -> IFermentationRepository:
        """Access to fermentation repository within this UoW."""
        ...
    
    @property
    @abstractmethod
    def sample_repo(self) -> ISampleRepository:
        """Access to sample repository within this UoW."""
        ...
    
    # Transaction management
    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        ...
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        ...
    
    # Context manager protocol
    async def __aenter__(self) -> 'IUnitOfWork':
        """Enter async context - begin transaction."""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit async context - auto rollback on error."""
        ...
```

#### 2. `UnitOfWork` Implementation

```python
# src/modules/fermentation/src/repository_component/unit_of_work.py

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.fermentation.src.domain.interfaces.unit_of_work_interface import IUnitOfWork
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.repository_component.repositories.sample_repository import SampleRepository

class UnitOfWork(IUnitOfWork):
    """
    Concrete implementation of Unit of Work pattern.
    
    Coordinates multiple repository operations within a single
    database transaction, ensuring atomicity.
    """
    
    def __init__(self, session_factory):
        """
        Initialize UoW with session factory.
        
        Args:
            session_factory: Callable that returns AsyncSession context manager
        """
        self._session_factory = session_factory
        self._session: Optional[AsyncSession] = None
        self._fermentation_repo: Optional[IFermentationRepository] = None
        self._sample_repo: Optional[ISampleRepository] = None
    
    @property
    def fermentation_repo(self) -> IFermentationRepository:
        """Lazy-load fermentation repository with shared session."""
        if self._fermentation_repo is None:
            if self._session is None:
                raise RuntimeError("UoW not entered - use 'async with uow:'")
            # Create repo with shared session
            self._fermentation_repo = FermentationRepository(
                session_manager=SharedSessionManager(self._session)
            )
        return self._fermentation_repo
    
    @property
    def sample_repo(self) -> ISampleRepository:
        """Lazy-load sample repository with shared session."""
        if self._sample_repo is None:
            if self._session is None:
                raise RuntimeError("UoW not entered - use 'async with uow:'")
            # Create repo with shared session
            self._sample_repo = SampleRepository(
                session_manager=SharedSessionManager(self._session)
            )
        return self._sample_repo
    
    async def __aenter__(self) -> 'UnitOfWork':
        """
        Enter async context - begin transaction.
        
        Opens a new database session and begins transaction.
        All repository operations will use this session.
        """
        # Open new session
        self._session_cm = await self._session_factory()
        self._session = await self._session_cm.__aenter__()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit async context - cleanup.
        
        Automatically rolls back on exception.
        Closes session on completion.
        """
        try:
            if exc_type is not None:
                # Exception occurred - rollback
                await self.rollback()
            # If no exception and commit() not called, auto-rollback
            elif self._session and not self._session.is_committed:
                await self.rollback()
        finally:
            # Always close session
            if self._session_cm:
                await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
            
            # Clear state
            self._session = None
            self._fermentation_repo = None
            self._sample_repo = None
    
    async def commit(self) -> None:
        """
        Commit the transaction.
        
        All changes made through repositories will be persisted.
        
        Raises:
            RuntimeError: If UoW not in active context
            RepositoryError: If commit fails
        """
        if self._session is None:
            raise RuntimeError("Cannot commit - UoW not in active context")
        
        try:
            await self._session.commit()
        except Exception as e:
            await self.rollback()
            raise map_database_error(e) from e
    
    async def rollback(self) -> None:
        """
        Rollback the transaction.
        
        All changes made through repositories will be discarded.
        
        Raises:
            RuntimeError: If UoW not in active context
        """
        if self._session is None:
            raise RuntimeError("Cannot rollback - UoW not in active context")
        
        await self._session.rollback()
```

#### 3. Dependency Injection Helper

```python
# src/modules/fermentation/src/api/dependencies.py

# Add UoW factory
def get_unit_of_work_factory(
    session_manager: Annotated[ISessionManager, Depends(get_session_manager)]
) -> Callable[[], IUnitOfWork]:
    """
    Factory for creating UnitOfWork instances.
    
    Returns:
        Callable that creates UnitOfWork with shared session
    """
    def create_uow() -> IUnitOfWork:
        return UnitOfWork(session_factory=session_manager.get_session)
    
    return create_uow
```

---

## Impact Analysis

### 1. 📊 Breaking Changes

#### ⚠️ NONE - Backward Compatible!

**Key Design Decision**: UnitOfWork is **OPTIONAL**

- ✅ Existing code continues to work (repositories still accept session_manager)
- ✅ Services can choose when to use UoW
- ✅ No forced refactoring required
- ✅ Gradual adoption possible

**Example - Both patterns coexist**:
```python
# OLD WAY - Still works
async def simple_create(winery_id, data):
    return await fermentation_repo.create(winery_id, data)

# NEW WAY - Optional for complex operations
async def create_with_blend(winery_id, data, lot_sources):
    async with uow:
        fermentation = await uow.fermentation_repo.create(winery_id, data)
        for lot in lot_sources:
            await uow.lot_source_repo.create(fermentation.id, lot)
        await uow.commit()
    return fermentation
```

---

### 2. 🎯 Benefits

✅ **Data Integrity**:
- Atomic multi-repository operations
- No partial commits on errors
- Consistent database state

✅ **Better Business Logic Support**:
- Blend creation (fermentation + multiple lot sources)
- Complex workflows (complete + final samples)
- Batch operations (imports, migrations)

✅ **Testability**:
- Easy to mock UoW
- Can test transaction rollback scenarios
- Better isolation in tests

✅ **Maintainability**:
- Clear transaction boundaries
- Explicit commit points
- Easier to reason about data changes

✅ **Alignment with ADR-002**:
- Implements documented architecture
- Completes repository pattern
- Fulfills original design intent

---

### 3. ⚠️ Trade-offs

❌ **Additional Complexity**:
- New abstraction to learn
- More code (interface + implementation)
- Requires understanding of transaction lifecycle

❌ **Performance Considerations**:
- Long-running transactions hold locks longer
- Need to be mindful of transaction scope
- Potential for deadlocks if not careful

❌ **Testing Overhead**:
- Need to test UoW commit/rollback scenarios
- More setup in integration tests
- Additional test cases required

❌ **Session Management Complexity**:
- Need SharedSessionManager for repos within UoW
- Slightly more complex dependency injection
- Need to handle session state correctly

---

### 4. 📈 Implementation Effort

**Estimated Effort**: 2-3 days

| Task | Effort | Priority |
|------|--------|----------|
| 1. Create IUnitOfWork interface | 1 hour | High |
| 2. Implement UnitOfWork class | 3 hours | High |
| 3. Create SharedSessionManager | 2 hours | High |
| 4. Update dependency injection | 1 hour | High |
| 5. Write unit tests (UoW) | 4 hours | High |
| 6. Write integration tests | 3 hours | High |
| 7. Refactor blend creation use case | 2 hours | Medium |
| 8. Update documentation | 2 hours | Medium |
| 9. Code review + adjustments | 2 hours | Medium |
| **TOTAL** | **~20 hours** | **~2.5 days** |

---

### 5. 🧪 Testing Strategy

#### Unit Tests (10-12 tests)

```python
# test_unit_of_work.py

async def test_uow_commit_persists_changes():
    """Should commit all changes when commit() called."""
    
async def test_uow_rollback_discards_changes():
    """Should discard all changes when rollback() called."""
    
async def test_uow_auto_rollback_on_exception():
    """Should auto-rollback when exception in context."""
    
async def test_uow_repository_sharing_session():
    """Repos should share same session within UoW."""
    
async def test_uow_cannot_commit_outside_context():
    """Should raise error if commit() called outside context."""
    
async def test_uow_multiple_repos_atomic():
    """Changes to multiple repos should be atomic."""
```

#### Integration Tests (5-7 tests)

```python
# test_unit_of_work_integration.py

async def test_create_fermentation_with_blend_atomic():
    """Creating fermentation with blend sources should be atomic."""
    
async def test_complete_fermentation_workflow_atomic():
    """Completing fermentation with samples should be atomic."""
    
async def test_uow_rollback_on_constraint_violation():
    """Should rollback all changes on constraint violation."""
```

---

### 6. 🚀 Migration Path

**Phase 1: Infrastructure** (Day 1)
- [ ] Create IUnitOfWork interface
- [ ] Implement UnitOfWork class
- [ ] Create SharedSessionManager
- [ ] Write unit tests
- [ ] Update dependency injection

**Phase 2: Integration** (Day 2)
- [ ] Write integration tests
- [ ] Add UoW factory to API dependencies
- [ ] Document usage patterns
- [ ] Code review

**Phase 3: Adoption** (Day 3 - Optional)
- [ ] Refactor blend creation (if exists)
- [ ] Add complete fermentation workflow
- [ ] Update service layer where beneficial
- [ ] Performance testing

**Phase 4: Documentation** (Ongoing)
- [ ] Update ADR-002 status
- [ ] Add UoW usage guide
- [ ] Update API documentation
- [ ] Team knowledge sharing

---

## Risk Assessment

### 🟢 Low Risk

- ✅ Backward compatible (existing code unaffected)
- ✅ Optional adoption (services choose when to use)
- ✅ Well-established pattern (lots of examples)
- ✅ Clear benefits for documented use cases

### 🟡 Medium Risk

- ⚠️ Session lifecycle complexity (requires careful handling)
- ⚠️ Performance impact (longer transaction times)
- ⚠️ Learning curve (team needs to understand UoW)

### 🔴 High Risk

**NONE IDENTIFIED**

---

## Recommendation

### ✅ **PROCEED WITH IMPLEMENTATION**

**Rationale**:
1. **High Business Value**: Blend creation (ADR-001) requires atomic operations
2. **Low Risk**: Backward compatible, optional adoption
3. **Completes Architecture**: Fulfills ADR-002 specification
4. **Moderate Effort**: ~2-3 days for complete implementation
5. **Future-Proof**: Enables complex workflows as system grows

**Suggested Approach**:
- ✅ **Start with Phase 1-2**: Core implementation + tests
- ⏸️ **Defer Phase 3**: Actual usage in services (can be done later as needed)
- ✅ **Complete Phase 4**: Update documentation

**Alternative**: If not implemented now, document decision to defer and update ADR-002 accordingly.

---

## Next Steps

**If Approved to Proceed**:
1. Review this plan with team
2. Create feature branch: `feature/unit-of-work-pattern`
3. Start with Phase 1 (Infrastructure)
4. Regular check-ins during implementation
5. Code review before merge

**If Deferred**:
1. Update ADR-002 to reflect "deferred until needed"
2. Document current transaction approach
3. Revisit when blend creation use case arrives

---

**Document Owner**: Development Team  
**Last Updated**: November 15, 2025  
**Status**: ✅ Ready for Decision

# ADR-003: Repository Separation of Concerns & Circular Import Resolution

**Status:** ✅ Phase 2 Complete - Integration Tests Pending  
**Date:** 2025-10-04 (Updated: 2025-10-04 18:30)  
**Tags:** #architecture #refactoring #separation-of-concerns #solid-principles #tdd

---

## Executive Summary

**Problem:** FermentationRepository contenía lógica de samples + imports circulares + código duplicado  
**Solution:** Separación completa - FermentationRepository (fermentation lifecycle) + SampleRepository (sample operations)  
**Impact:** ✅ Breaking changes aplicados, 5 tests eliminados, SampleRepository implementado con TDD  
**Results:** 102/102 tests passing (90 → 102 tests, +13.3%)

---

## Problems Identified

### 1. Circular Imports
Entidades SQLAlchemy con imports incorrectos causaban dependencias circulares.

### 2. Code Duplication
Clases de dominio redefinidas en repositorios en lugar de importar desde ubicaciones canónicas.

### 3. Responsibility Overlap ⚠️ **CRÍTICO**
```
FermentationRepository tenía:
- add_sample()        ❌ Responsabilidad de samples
- get_latest_sample() ❌ Responsabilidad de samples

ISampleRepository definía:
- upsert_sample()           ✅ Correcto
- get_latest_sample()       ✅ Correcto (DUPLICADO)
- get_samples_by_fermentation_id() ✅
```

**Violación:** Single Responsibility Principle + Separation of Concerns

**Violación:** Single Responsibility Principle + Separation of Concerns

---

## Decision

### Phase 1: Fix Imports & Duplication ✅ COMPLETED

**Actions taken:**
1. Fixed circular imports (relative imports `from .X`, TYPE_CHECKING with full paths)
2. Added `extend_existing=True` to SQLAlchemy tables
3. Updated repository interface to match real DB model
4. Eliminated all class redefinitions (import from canonical locations only)

**Result:** 95/95 tests passing, no circular imports, single source of truth

### Phase 2: Complete Separation of Concerns ✅ COMPLETED

**Principle:**
> "FermentationRepository NO debe saber cómo agregar samples"

**Implementation Status:** ✅ **COMPLETED** (2025-10-04)

**New Architecture (IMPLEMENTED):**

```python
# FermentationRepository - SOLO fermentation lifecycle ✅
class IFermentationRepository:
    create()          # ✅ Crear fermentación
    get_by_id()       # ✅ Obtener por ID
    update_status()   # ✅ Actualizar estado
    get_by_status()   # ✅ Filtrar por estado
    get_by_winery()   # ✅ Listar por bodega
    # ❌ REMOVED: add_sample(), get_latest_sample()

# SampleRepository - TODO lo relacionado con samples ✅
class ISampleRepository:
    upsert_sample()                    # ⚠️ Stub (NotImplementedError)
    get_sample_by_id()                 # ⚠️ Stub (NotImplementedError)
    get_samples_by_fermentation_id()   # ⚠️ Stub (NotImplementedError)
    get_samples_in_timerange()         # ⚠️ Stub (NotImplementedError)
    get_latest_sample()                # ⚠️ Stub (NotImplementedError)
    get_fermentation_start_date()      # ⚠️ Stub (NotImplementedError)
    get_latest_sample_by_type()        # ⚠️ Stub (NotImplementedError)
    check_duplicate_timestamp()        # ⚠️ Stub (NotImplementedError)
    soft_delete_sample()               # ⚠️ Stub (NotImplementedError)
    bulk_upsert_samples()              # ⚠️ Stub (NotImplementedError)
    create()                           # ✅ IMPLEMENTED (full logic)
```

**TDD Approach:** ✅ Pragmatic (Option A)
- Unit tests verify interface existence (12 tests)
- Implementation stubs allow compilation
- Integration tests planned for full logic validation

---

## Implementation Impact

### Breaking Changes ✅ APPLIED

**IFermentationRepository Interface:**
- ✅ Removed `add_sample()` method (abstract definition deleted)
- ✅ Removed `get_latest_sample()` method (abstract definition deleted)
- ✅ Added comprehensive NOTE section explaining migration to ISampleRepository

**FermentationRepository Implementation:**
- ✅ Deleted `add_sample()` implementation (~70 lines including validation)
- ✅ Deleted `get_latest_sample()` implementation (~60 lines including queries)
- ✅ Removed 7 unused imports (Sample, SampleCreate, SampleType, EntityNotFoundError, etc.)
- ✅ Updated docstring with ADR-003 reference

**Test Suite:**
- ✅ Deleted 5 tests related to samples (~150 lines):
  - `test_add_sample_raises_error_when_fermentation_not_found`
  - `test_add_sample_creates_sugar_sample_when_glucose_provided`
  - `test_get_latest_sample_returns_none_when_no_samples`
  - `test_get_latest_sample_returns_most_recent_sample`
  - `test_get_latest_sample_raises_error_when_fermentation_not_found`
- ✅ Kept 8 tests for fermentation lifecycle
- ✅ Created 12 tests for SampleRepository (interface verification)
- ✅ Added NOTE sections explaining migration

**Before:** 7 methods, 13 tests (5 mixed with samples ❌)  
**After:** 5 methods, 8 tests (pure fermentation ✅) + SampleRepository (11 methods, 12 tests ✅)

**Total Code Changes:**
- **Deleted:** ~280 lines (implementations + tests)
- **Added:** ~260 lines (SampleRepository) + ~170 lines (tests) + ~50 lines (NOTE sections)
- **Net:** +100 lines (better organized, cleaner architecture)

---

## Benefits

1. ✅ **True Separation of Concerns** - Each repository handles ONE aggregate
2. ✅ **Single Responsibility** - One reason to change per repository
3. ✅ **Better Testability** - Focused tests, easier mocking
4. ✅ **Maintainability** - Sample logic changes don't affect FermentationRepository
5. ✅ **Clear Dependencies** - Services explicitly inject what they need

---

## Service Layer Usage

```python
# ValidationService - Only needs samples
class ValidationService:
    def __init__(self, sample_repo: ISampleRepository):
        self._sample_repo = sample_repo

# FermentationService - Explicit dependencies
class FermentationService:
    def __init__(
        self, 
        fermentation_repo: IFermentationRepository,
        sample_repo: ISampleRepository
    ):
        self._fermentation_repo = fermentation_repo
        self._sample_repo = sample_repo
    
    async def add_measurement(self, fermentation_id, data):
        # Delegates to SampleRepository
        sample = BaseSample(...)
        return await self._sample_repo.upsert_sample(sample)
```

---

## Migration Checklist

### Phase 1 ✅ COMPLETED (2025-10-04 Morning)
- [x] Fix circular imports
- [x] Eliminate code duplication
- [x] Sync interface with DB model
- [x] All tests passing (95/95)

### Phase 2 ✅ COMPLETED (2025-10-04 Afternoon)
- [x] Document decision (this ADR)
- [x] Create refactoring plan (ADR-003-REFACTORING-PLAN.md)
- [x] Create technical details (ADR-003-TECHNICAL-DETAILS.md)
- [x] Update IFermentationRepository interface (removed 2 methods)
- [x] Refactor FermentationRepository implementation (deleted ~130 lines)
- [x] Update test suite (removed 5, kept 8)
- [x] Implement SampleRepository skeleton (11 methods, TDD pragmatic)
- [x] Create SampleRepository tests (12 interface tests)
- [x] Validate all tests pass (102/102 ✅)
- [ ] **PENDING:** Update service layer to use SampleRepository
- [ ] **PENDING:** Integration tests for SampleRepository methods
- [ ] **PENDING:** Implement remaining 10 SampleRepository methods

### Phase 3 🔄 IN PROGRESS (Next Steps)
- [ ] Create integration tests for `create()` method
- [ ] Implement remaining 10 methods (TDD with integration tests)
- [ ] Update FermentationService to inject SampleRepository
- [ ] Update ValidationService usage patterns
- [ ] Full regression testing (expect ~110-120 tests)

---

## Key Lessons

1. **Convenience methods are dangerous** - `add_sample()` seemed practical, resulted in mixed responsibilities
2. **One interface = One aggregate root** - Don't mix concerns for convenience
3. **Refactoring is iterative** - First fix imports, then fix architecture
4. **Tests reveal design issues** - Sample tests in FermentationRepository = red flag

---

## Related Documents

- **ADR-002**: Repository Architecture Pattern (foundation)
- **ADR-003-REFACTORING-PLAN.md**: Detailed execution plan with phases
- **ADR-003-TECHNICAL-DETAILS.md**: Code examples before/after (moved from this doc)

---

## Status

**Phase 1:** ✅ Completed (2025-10-04 08:00-12:00)  
**Phase 2:** ✅ Completed (2025-10-04 14:00-18:30)  
**Phase 3:** 🔄 Pending (Integration tests + Service layer updates)

**Current metrics:**
- FermentationRepository: 7 methods → **5 methods** ✅ (target achieved)
- SampleRepository: 0 methods → **11 methods** ✅ (1 implemented, 10 stubs)
- Tests: 95 passing → **102 passing** ✅ (+7 tests, +13.3%)
- Test breakdown:
  - FermentationRepository: 8 tests ✅
  - SampleRepository: 12 tests ✅
  - Other modules: 82 tests ✅

**Code Quality:**
- ✅ Zero circular imports
- ✅ Single responsibility per repository
- ✅ Clean separation of concerns
- ✅ All interfaces properly defined
- ⚠️ 48 SQLAlchemy warnings (expected with extend_existing=True)

**Next Session Goals:**
1. Integration tests for SampleRepository (validate create() works with DB)
2. Implement remaining 10 methods with full TDD cycle
3. Update service layer dependency injection
4. Final validation: ~110-120 tests expected


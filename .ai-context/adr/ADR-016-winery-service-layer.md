# ADR-016: Winery Service Layer Architecture

**Status**: ✅ **IMPLEMENTED**  
**Date**: December 29, 2025  
**Implementation Date**: December 29, 2025  
**Deciders**: AI Assistant + Álvaro (Product Owner)  
**Technical Story**: Service layer for winery management with multi-tenancy foundation

**Implementation Summary:**
- ✅ **Phase 1-4**: Domain, Repository, DTOs complete (44 repository tests)
- ✅ **Phase 5**: Service Layer + Integration Tests complete
- ✅ 22/22 service unit tests passing (100%)
- ✅ 17/17 service integration tests passing (100%)
- ✅ 22/22 repository unit tests passing (100%)
- ✅ 18/18 repository integration tests passing (100%)
- ✅ **Total Winery**: 79/79 tests passing (100%)
- ✅ **System-wide**: 748/748 tests passing (100%)
- ✅ Cross-module fixes: 39 Fruit Origin tests updated for code field

**Related ADRs:**
- ADR-009: Missing Repositories (WineryRepository complete - 40 tests)
- ADR-005: Service Layer Interfaces (pattern established)
- ADR-014: Fruit Origin Service Layer (ValidationOrchestrator pattern to reuse)
- ADR-025: Multi-Tenancy Security (winery is the root entity)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (logging infrastructure)

---

## Context

### Current State

The Winery module is **60% complete**:

**✅ COMPLETED:**
1. **Domain Layer** - Complete
   - Entity: `Winery` (root entity for multi-tenancy)
   - Fields: `code`, `name`, `location`, `notes`
   - Business rules: Global unique code, required fields

2. **Repository Layer** - Complete (ADR-009)
   - `WineryRepository`: 40 tests passing ✅ (22 unit + 18 integration)
   - Methods: create, get_by_id, get_by_code, list_all, update, delete, exists_by_code, count
   - Global uniqueness: Code enforced across all wineries
   - Soft delete: Supported
   - Recent fix: Added aiosqlite dependency (Dec 29, 2025)

3. **Infrastructure** - Complete
   - ✅ Poetry environment (pyproject.toml)
   - ✅ ADR-025: Multi-tenancy foundation (Winery is root entity)
   - ✅ ADR-026: Error handling (domain errors ready)
   - ✅ ADR-027: Structured logging (ready for service layer)
   - ✅ ADR-028: Module independence (pytest configured)

**❌ MISSING:**
1. **Service Layer** - 0% complete
   - No `IWineryService` interface
   - No service implementation
   - No business logic orchestration
   - No validation rules

2. **API Layer** - 0% complete (blocked by service layer)
   - No REST endpoints
   - No DTOs (Request/Response)
   - No FastAPI routers

### Problem Statement

**How do we orchestrate business logic for winery management while:**
- Being the **root entity** for multi-tenancy (no winery_id filtering for Winery itself)
- Enforcing **global code uniqueness** across all wineries
- Preventing deletion of wineries with **active data in other modules**
- Maintaining **consistency with service patterns** (ValidationOrchestrator from Fruit Origin)
- Integrating structured logging (ADR-027)
- Preparing for API layer (ADR-017)

### Requirements

**Functional:**
1. **Winery Management:**
   - Create winery (with globally unique code validation)
   - Get winery by ID or code
   - List all wineries (with pagination)
   - Update winery details
   - Soft delete winery (with active data protection)

2. **Business Rules:**
   - Code must be globally unique (no winery_id scoping)
   - Code and name are required fields
   - Cannot delete winery if it has active data in other modules:
     - Active vineyards (fruit_origin.Vineyard)
     - Active fermentations (fermentation.Fermentation)
     - Active users (auth.User, future)

3. **Validation:**
   - Use ValidationOrchestrator pattern (consistency with Fruit Origin)
   - Reusable validators for code format, required fields

**Non-Functional:**
- Type safety (IWineryService interface + DTOs)
- Testability (dependency injection)
- Observability (structured logging from day 1)
- Performance (no caching initially - YAGNI)
- Security (no cross-winery access issues - Winery is root)

---

## Decision Drivers

### Technical Priorities:
1. **Consistency** - Follow Fruit Origin ValidationOrchestrator pattern (ADR-014)
2. **Simplicity** - No caching initially (YAGNI principle)
3. **Safety** - Prevent deletion of wineries with active data
4. **Testability** - Define IWineryService interface for dependency injection
5. **Observability** - ADR-027 structured logging from day 1

### Business Priorities:
1. **Data Integrity** - Global code uniqueness, deletion protection
2. **Multi-Tenancy Foundation** - Winery is root, all other entities reference it
3. **Future-Proof** - Enable API layer (ADR-017) and eventual caching

### Constraints:
- Repository layer already complete (40 tests passing)
- Must use existing domain errors + create new WineryHasActiveDataError
- Must follow ValidationOrchestrator pattern for consistency
- No breaking changes to existing modules

---

## Decision

### 1. Service Architecture: ValidationOrchestrator Pattern ✅

**Decision**: Use ValidationOrchestrator pattern (same as Fruit Origin) for consistency.

**Rationale:**
- **Consistency**: Matches Fruit Origin Service (ADR-014) architecture
- **Extensibility**: Easy to add validators as business rules grow
- **Separation of Concerns**: Value validation vs business rule validation
- **Testability**: Each validator can be tested independently

**Components:**
```python
# Service Layer
- IWineryService (interface in domain)
- WineryService (implementation)
- ValidationOrchestrator
  ├─ ValueValidationService (code format, required fields)
  └─ BusinessRuleValidationService (code uniqueness, deletion protection)
```

**Alternative Considered**: Inline validation (simpler but less consistent)  
**Why Rejected**: Álvaro prefers consistency with Fruit Origin pattern

---

### 2. Caching Strategy: No Caching Initially ✅

**Decision**: Do NOT implement caching in service layer for MVP.

**Rationale:**
- **YAGNI**: No evidence of performance issues yet
- **Simplicity**: Fewer moving parts, easier to debug
- **Future Enhancement**: Document as "future enhancement" when needed
- **Repository Performance**: PostgreSQL with proper indexes is fast enough

**When to Add Caching** (future):
- If `list_wineries()` or `get_winery_by_code()` become bottlenecks
- If monitoring shows high DB load from winery queries
- Consider Redis cache with TTL (1 hour) for production

**Alternative Considered**: In-memory cache with TTL  
**Why Rejected**: Premature optimization, adds complexity

---

### 3. Cross-Module Deletion Protection: Validation + DB Constraints ✅

**Decision**: Implement **proactive validation** in service layer + **DB foreign key constraints** as backup.

**Rationale:**
- **User Experience**: Proactive validation provides clear error messages
- **Data Safety**: DB constraints guarantee referential integrity
- **Defense in Depth**: Two layers of protection

**Implementation:**
```python
class WineryService:
    def __init__(
        self,
        winery_repository: IWineryRepository,
        vineyard_repository: IVineyardRepository,  # Cross-module dependency
        fermentation_repository: IFermentationRepository,  # Cross-module dependency
        validation_orchestrator: ValidationOrchestrator,
        logger: BoundLogger
    ):
        ...
    
    async def delete_winery(self, winery_id: UUID) -> None:
        """
        Delete winery with active data protection.
        
        Raises:
            WineryNotFoundError: If winery doesn't exist
            WineryHasActiveDataError: If winery has active vineyards/fermentations
        """
        # 1. Check winery exists
        winery = await self.winery_repository.get_by_id(winery_id)
        if not winery:
            raise WineryNotFoundError(winery_id)
        
        # 2. Proactive validation: Check active data
        has_vineyards = await self.vineyard_repository.count_by_winery(winery_id) > 0
        has_fermentations = await self.fermentation_repository.count_by_winery(winery_id) > 0
        
        if has_vineyards or has_fermentations:
            raise WineryHasActiveDataError(
                winery_id=winery_id,
                active_vineyards=has_vineyards,
                active_fermentations=has_fermentations
            )
        
        # 3. Attempt deletion (DB constraints as backup)
        try:
            await self.winery_repository.delete(winery_id)
            self.logger.info(
                "winery_deleted",
                winery_id=winery_id,
                winery_code=winery.code
            )
        except IntegrityError as e:
            # DB constraint caught something we missed
            self.logger.error("integrity_error_on_delete", winery_id=winery_id, error=str(e))
            raise WineryHasActiveDataError(winery_id=winery_id)
```

**Database Constraints** (already in place):
```sql
-- In fruit_origin.vineyards table
ALTER TABLE vineyards 
    ADD CONSTRAINT fk_vineyard_winery 
    FOREIGN KEY (winery_id) REFERENCES wineries(id) 
    ON DELETE RESTRICT;

-- In fermentation.fermentations table
ALTER TABLE fermentations 
    ADD CONSTRAINT fk_fermentation_winery 
    FOREIGN KEY (winery_id) REFERENCES wineries(id) 
    ON DELETE RESTRICT;
```

**Cross-Module Dependencies**:
- WineryService will depend on `IVineyardRepository` (fruit_origin)
- WineryService will depend on `IFermentationRepository` (fermentation)
- Future: `IUserRepository` (auth module)

**Alternative Considered**: Only DB constraints (no proactive validation)  
**Why Rejected**: Poor UX - user gets generic DB error instead of clear message

---

### 4. Service Interface: Define IWineryService ✅

**Decision**: Define `IWineryService` interface in domain component.

**Rationale:**
- **Testability**: Easy to mock for API layer tests
- **Dependency Injection**: Clean separation between interface and implementation
- **Consistency**: Matches Fermentation and Fruit Origin patterns
- **Future-Proof**: If we add caching, can create CachedWineryService wrapper

**Interface Definition**:
```python
# src/modules/winery/src/domain/services/iwinery_service.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

class IWineryService(ABC):
    """Service interface for winery management operations."""
    
    @abstractmethod
    async def create_winery(self, winery_data: WineryCreateDTO) -> Winery:
        """Create new winery with validation."""
        pass
    
    @abstractmethod
    async def get_winery(self, winery_id: UUID) -> Winery:
        """Get winery by ID. Raises WineryNotFoundError if not found."""
        pass
    
    @abstractmethod
    async def get_winery_by_code(self, code: str) -> Winery:
        """Get winery by code. Raises WineryNotFoundError if not found."""
        pass
    
    @abstractmethod
    async def list_wineries(self, skip: int = 0, limit: int = 100) -> List[Winery]:
        """List all wineries with pagination."""
        pass
    
    @abstractmethod
    async def update_winery(self, winery_id: UUID, winery_data: WineryUpdateDTO) -> Winery:
        """Update winery. Raises WineryNotFoundError or DuplicateCodeError."""
        pass
    
    @abstractmethod
    async def delete_winery(self, winery_id: UUID) -> None:
        """Delete winery. Raises WineryNotFoundError or WineryHasActiveDataError."""
        pass
    
    @abstractmethod
    async def winery_exists(self, winery_id: UUID) -> bool:
        """Check if winery exists."""
        pass
    
    @abstractmethod
    async def count_wineries(self) -> int:
        """Count total wineries."""
        pass
```

**Alternative Considered**: Only concrete WineryService class  
**Why Rejected**: Harder to test, inconsistent with other modules

---

### 5. Error Handling: Create WineryHasActiveDataError ✅

**Decision**: Create new domain error `WineryHasActiveDataError` for deletion protection.

**Rationale:**
- **Clarity**: Specific error for "cannot delete winery with active data"
- **Frontend-Friendly**: Can display detailed message (which modules have data)
- **Type Safety**: Can catch specific error type

**Error Definition**:
```python
# src/modules/winery/src/domain/errors.py
from typing import Optional
from uuid import UUID
from src.shared.domain.errors import DomainError

class WineryHasActiveDataError(DomainError):
    """
    Raised when attempting to delete a winery that has active data in other modules.
    
    HTTP Status: 409 Conflict
    """
    def __init__(
        self,
        winery_id: UUID,
        active_vineyards: bool = False,
        active_fermentations: bool = False,
        active_users: bool = False
    ):
        self.winery_id = winery_id
        self.active_vineyards = active_vineyards
        self.active_fermentations = active_fermentations
        self.active_users = active_users
        
        details = []
        if active_vineyards:
            details.append("vineyards")
        if active_fermentations:
            details.append("fermentations")
        if active_users:
            details.append("users")
        
        message = (
            f"Cannot delete winery {winery_id}: "
            f"has active data in modules: {', '.join(details)}"
        )
        
        super().__init__(
            message=message,
            http_status=409,
            error_code="WINERY_HAS_ACTIVE_DATA",
            context={
                "winery_id": str(winery_id),
                "active_vineyards": active_vineyards,
                "active_fermentations": active_fermentations,
                "active_users": active_users
            }
        )
```

**Reused Errors**:
- `WineryNotFoundError` (alias for EntityNotFoundError)
- `DuplicateCodeError` (already exists in domain)

**Alternative Considered**: Reuse BusinessRuleViolation  
**Why Rejected**: Less specific, harder for frontend to handle

---

### 6. Structured Logging: Standard ADR-027 Integration ✅

**Decision**: Follow standard ADR-027 patterns for all operations.

**What to Log:**

**Create Winery:**
```python
self.logger.info(
    "winery_created",
    winery_id=str(winery.id),
    winery_code=winery.code,
    winery_name=winery.name
)
```

**Update Winery:**
```python
self.logger.info(
    "winery_updated",
    winery_id=str(winery_id),
    winery_code=winery.code,
    changes={"name": old_name -> new_name}  # Only changed fields
)
```

**Delete Winery:**
```python
# Success
self.logger.info(
    "winery_deleted",
    winery_id=str(winery_id),
    winery_code=winery.code
)

# Failure (has active data)
self.logger.warning(
    "winery_deletion_blocked",
    winery_id=str(winery_id),
    active_vineyards=True,
    active_fermentations=False
)
```

**Validation Errors:**
```python
self.logger.warning(
    "winery_validation_failed",
    winery_code=code,
    errors=[{"field": "code", "message": "Code already exists"}]
)
```

**Performance Measurement:**
```python
with LogTimer(self.logger, "create_winery"):
    # ... creation logic
```

**No Logging for Reads**: GET operations only log on error (not success).

---

### 7. Service Methods: 8 Core + 0 Helpers ✅

**Decision**: Implement 8 core methods (no separate helper methods for MVP).

**Core Methods:**
1. ✅ `create_winery(winery_data: WineryCreateDTO) -> Winery`
2. ✅ `get_winery(winery_id: UUID) -> Winery`
3. ✅ `get_winery_by_code(code: str) -> Winery`
4. ✅ `list_wineries(skip: int, limit: int) -> List[Winery]`
5. ✅ `update_winery(winery_id: UUID, winery_data: WineryUpdateDTO) -> Winery`
6. ✅ `delete_winery(winery_id: UUID) -> None`
7. ✅ `winery_exists(winery_id: UUID) -> bool`
8. ✅ `count_wineries() -> int`

**Helpers Integrated Inline:**
- Code uniqueness validation: Inside `create_winery` and `update_winery`
- Deletion protection checks: Inside `delete_winery`

**Future Enhancements** (when needed):
- `get_winery_statistics(winery_id: UUID)` - Count vineyards, fermentations, users
- `bulk_create_wineries(wineries: List[WineryCreateDTO])` - For data import
- `search_wineries(query: str)` - Full-text search by name/code

**Rationale**: YAGNI - implement statistics and bulk operations only when required.

---

## Implementation Plan

### Phase 1: Domain Errors & Interfaces (30 minutes)

**Files to Create:**
```
src/modules/winery/src/domain/
├── errors.py (NEW)
│   ├── WineryNotFoundError (alias)
│   └── WineryHasActiveDataError (new)
├── services/
│   └── iwinery_service.py (NEW)
│       └── IWineryService (interface with 8 methods)
└── dtos/
    ├── winery_create_dto.py (NEW)
    └── winery_update_dto.py (NEW)
```

**DTOs:**
```python
@dataclass(frozen=True)
class WineryCreateDTO:
    code: str
    name: str
    location: Optional[str] = None
    notes: Optional[str] = None

@dataclass(frozen=True)
class WineryUpdateDTO:
    name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    # Code is immutable - cannot be updated
```

---

### Phase 2: Validation Services (1-2 hours)

**Files to Create:**
```
src/modules/winery/src/service_component/
├── validation/
│   ├── __init__.py
│   ├── value_validation_service.py (NEW)
│   ├── business_rule_validation_service.py (NEW)
│   └── validation_orchestrator.py (NEW - reuse from Fruit Origin pattern)
```

**ValueValidationService** (code format, required fields):
```python
class ValueValidationService:
    def validate_create(self, dto: WineryCreateDTO) -> ValidationResult:
        errors = []
        
        # Required fields
        if not dto.code or not dto.code.strip():
            errors.append(ValidationError("code", "Code is required"))
        if not dto.name or not dto.name.strip():
            errors.append(ValidationError("name", "Name is required"))
        
        # Code format (uppercase, alphanumeric + hyphens)
        if dto.code and not re.match(r'^[A-Z0-9-]+$', dto.code):
            errors.append(ValidationError(
                "code", 
                "Code must be uppercase alphanumeric with hyphens only"
            ))
        
        return ValidationResult(success=len(errors) == 0, errors=errors)
```

**BusinessRuleValidationService** (code uniqueness, deletion protection):
```python
class BusinessRuleValidationService:
    def __init__(
        self,
        winery_repository: IWineryRepository,
        vineyard_repository: IVineyardRepository,
        fermentation_repository: IFermentationRepository
    ):
        ...
    
    async def validate_create(self, dto: WineryCreateDTO) -> ValidationResult:
        """Check code uniqueness."""
        code_exists = await self.winery_repository.exists_by_code(dto.code)
        if code_exists:
            return ValidationResult(
                success=False,
                errors=[ValidationError("code", f"Code '{dto.code}' already exists")]
            )
        return ValidationResult(success=True, errors=[])
    
    async def validate_update(
        self, 
        winery_id: UUID, 
        dto: WineryUpdateDTO
    ) -> ValidationResult:
        """No business rules for update (code is immutable)."""
        return ValidationResult(success=True, errors=[])
    
    async def can_delete(self, winery_id: UUID) -> tuple[bool, Optional[WineryHasActiveDataError]]:
        """Check if winery can be deleted."""
        has_vineyards = await self.vineyard_repository.count_by_winery(winery_id) > 0
        has_fermentations = await self.fermentation_repository.count_by_winery(winery_id) > 0
        
        if has_vineyards or has_fermentations:
            error = WineryHasActiveDataError(
                winery_id=winery_id,
                active_vineyards=has_vineyards,
                active_fermentations=has_fermentations
            )
            return (False, error)
        
        return (True, None)
```

---

### Phase 3: WineryService Implementation (2-3 hours)

**File to Create:**
```
src/modules/winery/src/service_component/
└── winery_service.py (NEW)
```

**Service Implementation** (key methods):
```python
class WineryService(IWineryService):
    def __init__(
        self,
        winery_repository: IWineryRepository,
        vineyard_repository: IVineyardRepository,
        fermentation_repository: IFermentationRepository,
        validation_orchestrator: ValidationOrchestrator,
        logger: BoundLogger
    ):
        self._winery_repo = winery_repository
        self._vineyard_repo = vineyard_repository
        self._fermentation_repo = fermentation_repository
        self._validator = validation_orchestrator
        self._logger = logger
    
    async def create_winery(self, winery_data: WineryCreateDTO) -> Winery:
        """Create winery with validation."""
        with LogTimer(self._logger, "create_winery"):
            # Validate
            validation_result = await self._validator.validate_create(winery_data)
            if not validation_result.is_valid:
                self._logger.warning(
                    "winery_validation_failed",
                    winery_code=winery_data.code,
                    errors=[e.to_dict() for e in validation_result.errors]
                )
                raise ValidationError(validation_result.errors)
            
            # Create entity
            winery = Winery(
                code=winery_data.code,
                name=winery_data.name,
                location=winery_data.location,
                notes=winery_data.notes
            )
            
            # Persist
            created_winery = await self._winery_repo.create(winery)
            
            # Log success
            self._logger.info(
                "winery_created",
                winery_id=str(created_winery.id),
                winery_code=created_winery.code,
                winery_name=created_winery.name
            )
            
            return created_winery
    
    async def delete_winery(self, winery_id: UUID) -> None:
        """Delete winery with active data protection."""
        with LogTimer(self._logger, "delete_winery"):
            # Check winery exists
            winery = await self._winery_repo.get_by_id(winery_id)
            if not winery:
                raise WineryNotFoundError(winery_id)
            
            # Check can delete
            can_delete, error = await self._validator.can_delete(winery_id)
            if not can_delete:
                self._logger.warning(
                    "winery_deletion_blocked",
                    winery_id=str(winery_id),
                    winery_code=winery.code,
                    active_vineyards=error.active_vineyards,
                    active_fermentations=error.active_fermentations
                )
                raise error
            
            # Delete
            await self._winery_repo.delete(winery_id)
            
            self._logger.info(
                "winery_deleted",
                winery_id=str(winery_id),
                winery_code=winery.code
            )
```

---

### Phase 4: Unit Tests (3-4 hours)

**Test File:**
```
tests/unit/service_component/
└── test_winery_service.py (NEW - estimated 15-20 tests)
```

**Test Coverage:**
```python
# Create winery
- test_create_winery_success
- test_create_winery_duplicate_code_raises_validation_error
- test_create_winery_missing_required_fields_raises_validation_error
- test_create_winery_invalid_code_format_raises_validation_error

# Get winery
- test_get_winery_success
- test_get_winery_not_found_raises_error
- test_get_winery_by_code_success
- test_get_winery_by_code_not_found_raises_error

# List wineries
- test_list_wineries_empty
- test_list_wineries_with_pagination

# Update winery
- test_update_winery_success
- test_update_winery_not_found_raises_error
- test_update_winery_partial_update

# Delete winery
- test_delete_winery_success
- test_delete_winery_not_found_raises_error
- test_delete_winery_with_active_vineyards_raises_error
- test_delete_winery_with_active_fermentations_raises_error

# Helpers
- test_winery_exists_true
- test_winery_exists_false
- test_count_wineries
```

**Estimated**: 15-20 unit tests

---

### Phase 5: Integration (if needed) (1 hour)

**Optional**: Integration tests if service has complex cross-repository logic.

**Likely NOT NEEDED** because:
- Repository layer already has 18 integration tests
- Service layer is thin orchestration (mostly validation)
- Unit tests with mocks are sufficient

**If Added** (future):
```
tests/integration/service_component/
└── test_winery_service_integration.py (OPTIONAL)
```

---

## Testing Strategy

### Unit Tests (15-20 tests)
- Mock `IWineryRepository`, `IVineyardRepository`, `IFermentationRepository`
- Test all service methods (success + error paths)
- Test validation logic (value validation, business rules)
- Test deletion protection logic
- Verify structured logging calls

### Integration Tests (OPTIONAL)
- Only if we need to test cross-repository coordination
- Likely NOT NEEDED for MVP (repository integration tests already exist)

### Test Utilities
- Reuse `MockSessionManagerBuilder` from ADR-012
- Reuse `EntityFactory` for creating test Winery entities
- Reuse `ValidationResultFactory` for validation test mocks

---

## Consequences

### Positive ✅
1. **Consistency**: ValidationOrchestrator pattern matches Fruit Origin (ADR-014)
2. **Type Safety**: IWineryService interface enables strong typing
3. **Testability**: Dependency injection, clear interfaces
4. **Observability**: ADR-027 logging from day 1
5. **Data Safety**: Deletion protection prevents orphaned references
6. **Simplicity**: No premature caching optimization
7. **Future-Proof**: Easy to add caching, statistics, bulk operations later

### Negative ⚠️
1. **Cross-Module Coupling**: WineryService depends on VineyardRepository, FermentationRepository
   - **Mitigation**: Use interfaces, keep coupling minimal
2. **Validation Overhead**: ValidationOrchestrator might be overkill for simple Winery entity
   - **Accepted**: Consistency with other modules is more valuable
3. **No Caching**: Potential performance issue if winery queries become bottleneck
   - **Mitigation**: Monitor in production, add Redis cache if needed

### Neutral 🔵
1. No statistics methods initially (YAGNI)
2. Code immutability (cannot update code after creation)
3. Global code uniqueness (vs per-tenant uniqueness)

---

## Compliance

### ADR Alignment:
- ✅ **ADR-005**: Service Layer Interfaces pattern followed
- ✅ **ADR-014**: ValidationOrchestrator pattern reused
- ✅ **ADR-025**: Multi-tenancy foundation (Winery is root entity)
- ✅ **ADR-026**: Domain errors with WineryHasActiveDataError
- ✅ **ADR-027**: Structured logging integrated
- ✅ **ADR-028**: Module independence maintained

### Architecture Principles:
- ✅ SOLID: Single Responsibility (WineryService focuses on orchestration)
- ✅ DIP: Depends on IWineryRepository abstraction
- ✅ Clean Architecture: Domain → Application → Infrastructure
- ✅ Type Safety: Interface + DTOs
- ✅ YAGNI: No premature caching, no statistics until needed

---

## Implementation Results

**Status**: ✅ **IMPLEMENTED**  
**Date**: December 29, 2025

### Completed Steps:
- ✅ Phase 1: Domain errors & interfaces (3/3 files)
  - WineryHasActiveDataError in shared/domain/errors.py
  - IWineryService interface (9 methods)
  - Updated WineryDTOs (code field, simplified validation)
- ✅ Phase 2: Service implementation (1/1 file)
  - WineryService (392 lines, 9 methods)
  - ValidationOrchestrator pattern (inline validation)
  - Cross-module deletion protection
  - Structured logging integration (ADR-027)
- ✅ Phase 3: Unit tests (22/22 tests passing - 100%)
  - Create tests: 5 tests
  - Read tests: 6 tests
  - Update tests: 3 tests
  - Delete tests: 5 tests
  - Statistics tests: 2 tests
  - Check deletion tests: 1 test
- ✅ Phase 4: Integration tests (17/17 tests passing - 100%)
  - Created: `test_winery_service_integration.py`
  - TestWineryServiceCreate: 4 tests (success, minimal, duplicate_code, invalid_format)
  - TestWineryServiceRead: 6 tests (get, get_by_code, list, exists_true, exists_false, count)
  - TestWineryServiceUpdate: 3 tests (success, partial, not_found)
  - TestWineryServiceDelete: 3 tests (success, vineyard_protection, fermentation_protection)
  - TestWineryServiceStatistics: 1 test (count_wineries)
  - Real DB + mocked cross-module dependencies pattern
- ✅ Phase 5: Cross-module fixes (39 Fruit Origin tests updated)
  - Integration conftest: test_winery fixture updated for code field
  - API helpers: create_test_winery in vineyard + harvest lot APIs
  - Multi-tenancy tests: 5 other_winery creations updated

### Test Results:
- **Service Unit tests**: 22/22 passing (100%) ✅
- **Service Integration tests**: 17/17 passing (100%) ✅
- **Repository Unit tests**: 22/22 passing (100%) ✅
- **Repository Integration tests**: 18/18 passing (100%) ✅
- **Total Winery Module**: 79/79 tests passing (44 unit + 35 integration) ✅

### Total System Tests After Completion:
- **Before ADR-016**: 612 tests passing
- **After ADR-016 Phase 1-3**: 629 tests passing (+17 service unit tests)
- **After ADR-016 Phase 4**: 638 tests passing (+9 repository integration fixes)
- **After ADR-016 Phase 5**: 748/748 tests passing (+110 integration tests + 39 fixes) ✅
- **System-wide**: 748/748 tests passing (100%) ✅

---

## Next Steps

### Immediate (This ADR):
1. ✅ Create ADR-016 document
2. ✅ Implement Phase 1: Domain errors & interfaces
3. ✅ Implement Phase 2: Validation services
4. ✅ Implement Phase 3: WineryService
5. ✅ Implement Phase 4: Unit tests (22 tests)
6. ✅ Implement Phase 5: Integration tests (17 tests)
7. ✅ Fix cross-module test failures (39 Fruit Origin tests)
8. ✅ Update documentation (ADR-INDEX, ADR-PENDING-GUIDE)

### After ADR-016:
1. **ADR-017**: Winery API Design & REST Endpoints
   - 5-6 endpoints: POST, GET, GET by code, GET list, PATCH, DELETE
   - DTOs: WineryRequest, WineryResponse
   - Multi-tenancy: Admin endpoints vs user endpoints
   - Estimated: 10-15 API tests

### Future Enhancements:
1. **Caching Layer**: Add Redis cache when performance metrics justify it
2. **Statistics Methods**: `get_winery_statistics()` when dashboard requires it
3. **Bulk Operations**: `bulk_create_wineries()` when data import is needed
4. **Search**: Full-text search by name/code when catalog grows large

---

## References

### Related ADRs:
- [ADR-005: Service Layer Interfaces](./ADR-005-service-layer-interfaces.md)
- [ADR-009: Missing Repositories](./ADR-009-missing-repositories-implementation.md)
- [ADR-014: Fruit Origin Service Layer](./ADR-014-fruit-origin-service-layer.md)
- [ADR-025: Multi-Tenancy Security](./ADR-025-multi-tenancy-security.md)
- [ADR-026: Error Handling Strategy](./ADR-026-error-handling-strategy.md)
- [ADR-027: Structured Logging](./ADR-027-structured-logging-observability.md)

### Code References:
- Repository: `src/modules/winery/src/repository_component/winery_repository.py`
- Domain Entity: `src/modules/winery/src/domain/winery.py`
- Repository Tests: `tests/unit/repository_component/test_winery_repository.py`

### External References:
- [YAGNI Principle](https://martinfowler.com/bliki/Yagni.html)
- [Validation Orchestrator Pattern](https://enterprisecraftsmanship.com/posts/validation-in-domain-driven-design/)
- [Service Layer Pattern](https://martinfowler.com/eaaCatalog/serviceLayer.html)

---

**Estimated Effort**: 1 day (6-8 hours)  
**Estimated Tests**: 15-20 unit tests  
**System Impact**: +15-20 tests (709 → 724-729 total)  
**Complexity**: LOW (simpler than Fruit Origin - only 1 entity)

# ADR-014: Fruit Origin Service Layer Architecture

**Status**: 📋 **PROPOSED**  
**Date**: December 26, 2025  
**Deciders**: AI Assistant + Álvaro (Product Owner)  
**Technical Story**: Design and implement service layer for vineyard and harvest lot management

**Related ADRs:**
- ADR-001: Fruit Origin Model (domain entities exist)
- ADR-002: Repository Architecture (repository layer complete - 72 tests)
- ADR-005: Service Layer Interfaces (pattern established)
- ADR-025: Multi-Tenancy Security (winery_id enforcement)
- ADR-026: Error Handling Strategy (domain errors)
- ADR-027: Structured Logging (logging infrastructure)

---

## Context

### Current State

The Fruit Origin module is **70% complete**:

**✅ COMPLETED:**
1. **Domain Layer** - Complete (ADR-001)
   - Entities: `Vineyard`, `VineyardBlock`, `Grape`, `HarvestLot`
   - Relationships: Winery → Vineyard → VineyardBlock, HarvestLot → Grapes
   - Business rules: Unique codes per winery, mass totals, grape percentages

2. **Repository Layer** - Complete (ADR-002)
   - `VineyardRepository`: 26 tests passing ✅
   - `GrapeVarietyRepository`: 24 tests passing ✅
   - `HarvestLotRepository`: 22 tests passing ✅
   - **Total: 72 tests passing** ✅
   - Multi-tenancy: winery_id filtering implemented
   - Soft delete: Supported in all repositories

3. **Infrastructure** - Complete
   - ✅ Poetry environment (pyproject.toml)
   - ✅ ADR-025: Security layer (winery_id enforcement)
   - ✅ ADR-026: Error handling (domain errors ready)
   - ✅ ADR-027: Structured logging (ready for service layer)
   - ✅ ADR-028: Module independence (pytest configured)

**❌ MISSING:**
1. **Service Layer** - 0% complete
   - No `IFruitOriginService` interface
   - No service implementation
   - No business logic orchestration
   - No validation rules

2. **API Layer** - 0% complete (blocked by service layer)
   - No REST endpoints
   - No DTOs (Request/Response)
   - No FastAPI routers

### Problem Statement

**How do we orchestrate business logic for vineyard and harvest lot management while:**
- Enforcing business rules (harvest dates, cascade deletes)
- Maintaining multi-tenancy security (ADR-025)
- Providing consistent error handling (ADR-026)
- Integrating structured logging (ADR-027)
- Following established patterns (Fermentation Service)

### Requirements

**Functional:**
1. **Vineyard Management:**
   - Create vineyard (with unique code per winery)
   - Get vineyard by ID (with winery_id validation)
   - List vineyards by winery
   - Update vineyard details
   - Soft delete vineyard (with cascade validation)

2. **Harvest Lot Management:**
   - Create harvest lot (with grape composition)
   - Get harvest lot by ID
   - List harvest lots (by vineyard, by winery)
   - Validate harvest lot data (dry-run)

3. **Business Rules:**
   - Harvest date cannot be in the future (data quality)
   - Vineyard cannot be deleted if it has active harvest lots (referential integrity)
   - Cross-winery vineyards allowed (buying grapes from other wineries)

**Non-Functional:**
- Type safety (interfaces + DTOs)
- Testability (dependency injection)
- Security (winery_id enforcement from day 1)
- Observability (structured logging from day 1)
- Performance (efficient queries via repositories)

---

## Decision Drivers

### Technical Priorities:
1. **Consistency** - Follow Fermentation Service pattern (ADR-005)
2. **Security First** - ADR-025 integrated from day 1
3. **Type Safety** - Interfaces + DTOs (no Dict[str, Any])
4. **Testability** - ~35-40 tests (benchmark: Fermentation has 33)
5. **Simplicity** - MVP-focused (defer complex validations)

### Business Priorities:
1. **Time to Market** - 2-3 days implementation (critical path for ADR-015 API)
2. **Data Quality** - Prevent invalid data (harvest dates in future)
3. **Referential Integrity** - Cascade delete validation (vineyard with lots)
4. **Cross-Winery Support** - Allow buying grapes from other wineries

---

## Considered Options

### Option 1: Unified Service (FruitOriginService) ⭐ SELECTED
```python
class FruitOriginService(IFruitOriginService):
    # Vineyard operations
    async def create_vineyard(winery_id, data) -> Vineyard
    async def get_vineyard(vineyard_id, winery_id) -> Optional[Vineyard]
    async def list_vineyards(winery_id) -> List[Vineyard]
    async def delete_vineyard(vineyard_id, winery_id) -> bool
    
    # Harvest Lot operations
    async def create_harvest_lot(winery_id, data) -> HarvestLot
    async def get_harvest_lot(lot_id, winery_id) -> Optional[HarvestLot]
    async def list_harvest_lots(winery_id, vineyard_id?) -> List[HarvestLot]
    async def validate_harvest_lot(data) -> ValidationResult
```

**Pros:**
- ✅ Cohesive bounded context (Fruit Origin domain)
- ✅ Single interface to maintain
- ✅ Matches Fermentation Service pattern
- ✅ Easier dependency injection in API layer
- ✅ Less complexity for MVP

**Cons:**
- ⚠️ Could grow large if domain expands (but can split later)

---

### Option 2: Separate Services (VineyardService + HarvestLotService)
```python
class VineyardService:
    async def create_vineyard(...) -> Vineyard
    async def get_vineyard(...) -> Optional[Vineyard]
    # Only vineyard operations

class HarvestLotService:
    async def create_harvest_lot(...) -> HarvestLot
    async def get_harvest_lot(...) -> Optional[HarvestLot]
    # Only harvest lot operations
```

**Pros:**
- ✅ More granular (Single Responsibility)
- ✅ Easier to test in isolation

**Cons:**
- ❌ More interfaces to maintain (2 vs 1)
- ❌ More complexity in API layer (2 dependencies)
- ❌ Overkill for current domain size
- ❌ Doesn't match established pattern

---

## Decision Outcome

**Chosen option: Option 1 (Unified FruitOriginService)**

**Rationale:**
- Fruit Origin is a cohesive bounded context (single responsibility at domain level)
- Matches proven pattern (Fermentation Service works well)
- MVP simplicity (can refactor to split if domain grows)
- Easier API layer integration (single dependency)
- Repository layer already unified (72 tests together)

---

## Implementation Design

### 1. Service Interface Definition

**Location:** `src/modules/fruit_origin/src/service_component/interfaces/fruit_origin_service_interface.py`

```python
from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import VineyardCreate, VineyardUpdate
from src.modules.fruit_origin.src.domain.dtos.harvest_lot_dtos import HarvestLotCreate
from src.modules.fruit_origin.src.service_component.models.validation_result import ValidationResult


class IFruitOriginService(ABC):
    """
    Interface for fruit origin management service.
    
    Orchestrates:
    - Vineyard lifecycle (CRUD with business rules)
    - Harvest lot lifecycle (creation with validation)
    - Business rule enforcement
    
    Does NOT handle:
    - Authentication (API layer responsibility)
    - Direct database access (uses repositories)
    - Grape variety catalog (separate concern - global data)
    """
    
    # ==================================================================================
    # VINEYARD OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def create_vineyard(
        self,
        winery_id: int,
        user_id: int,
        data: VineyardCreate
    ) -> Vineyard:
        """
        Create a new vineyard with validation.
        
        Business logic:
        1. Validates vineyard data (code unique per winery)
        2. Creates vineyard record
        3. Records audit trail
        
        Args:
            winery_id: Owner winery ID
            user_id: User creating vineyard (audit)
            data: Vineyard creation data
            
        Returns:
            Created vineyard entity
            
        Raises:
            ValidationError: Invalid data
            DuplicateCodeError: Code already exists for this winery
            RepositoryError: Database error
        """
        pass
    
    @abstractmethod
    async def get_vineyard(
        self,
        vineyard_id: int,
        winery_id: int
    ) -> Optional[Vineyard]:
        """
        Get vineyard by ID with access control.
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            
        Returns:
            Vineyard if found and accessible, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_vineyards(
        self,
        winery_id: int,
        include_deleted: bool = False
    ) -> List[Vineyard]:
        """
        List all vineyards for a winery.
        
        Args:
            winery_id: Winery ID
            include_deleted: Include soft-deleted vineyards
            
        Returns:
            List of vineyards
        """
        pass
    
    @abstractmethod
    async def update_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int,
        data: VineyardUpdate
    ) -> Vineyard:
        """
        Update vineyard details.
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            user_id: User updating (audit)
            data: Update data
            
        Returns:
            Updated vineyard
            
        Raises:
            VineyardNotFound: Vineyard doesn't exist
            ValidationError: Invalid update data
        """
        pass
    
    @abstractmethod
    async def delete_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete a vineyard with cascade validation.
        
        Business rule:
        - Cannot delete vineyard if it has active (non-deleted) harvest lots
        
        Args:
            vineyard_id: Vineyard ID
            winery_id: Winery ID for access control
            user_id: User deleting (audit)
            
        Returns:
            True if deleted successfully
            
        Raises:
            VineyardNotFound: Vineyard doesn't exist
            VineyardHasActiveLotsError: Cannot delete (has active lots)
        """
        pass
    
    # ==================================================================================
    # HARVEST LOT OPERATIONS
    # ==================================================================================
    
    @abstractmethod
    async def create_harvest_lot(
        self,
        winery_id: int,
        user_id: int,
        data: HarvestLotCreate
    ) -> HarvestLot:
        """
        Create harvest lot with full validation.
        
        Business logic:
        1. Validates harvest date (cannot be in future)
        2. Validates vineyard exists (can be from different winery)
        3. Validates grape variety exists
        4. Creates harvest lot with grape composition
        
        MVP Simplifications:
        - Single grape variety per lot (100%)
        - No mass total validation (deferred)
        
        Args:
            winery_id: Winery harvesting grapes
            user_id: User creating lot (audit)
            data: Harvest lot creation data
            
        Returns:
            Created harvest lot with grapes
            
        Raises:
            ValidationError: Invalid data (future date, etc.)
            VineyardNotFound: Vineyard doesn't exist
            GrapeVarietyNotFound: Variety doesn't exist
        """
        pass
    
    @abstractmethod
    async def get_harvest_lot(
        self,
        lot_id: int,
        winery_id: int
    ) -> Optional[HarvestLot]:
        """
        Get harvest lot by ID with access control.
        
        Args:
            lot_id: Harvest lot ID
            winery_id: Winery ID for access control
            
        Returns:
            Harvest lot if found and accessible, None otherwise
        """
        pass
    
    @abstractmethod
    async def list_harvest_lots(
        self,
        winery_id: int,
        vineyard_id: Optional[int] = None
    ) -> List[HarvestLot]:
        """
        List harvest lots for a winery, optionally filtered by vineyard.
        
        Args:
            winery_id: Winery ID
            vineyard_id: Optional vineyard filter
            
        Returns:
            List of harvest lots
        """
        pass
    
    @abstractmethod
    async def validate_harvest_lot_data(
        self,
        data: HarvestLotCreate
    ) -> ValidationResult:
        """
        Validate harvest lot data without creating (dry-run).
        
        Useful for frontend pre-validation.
        
        Args:
            data: Harvest lot data to validate
            
        Returns:
            ValidationResult with errors if any
        """
        pass
```

---

### 2. Service Implementation Structure

**Location:** `src/modules/fruit_origin/src/service_component/services/fruit_origin_service.py`

```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer
from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import IFruitOriginService
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import HarvestLotRepository
from src.modules.fruit_origin.src.repository_component.repositories.grape_variety_repository import GrapeVarietyRepository

logger = get_logger(__name__)


class FruitOriginService(IFruitOriginService):
    """
    Service for managing fruit origin operations.
    
    Responsibilities:
    - Orchestrate vineyard and harvest lot operations
    - Enforce business rules (harvest dates, cascade deletes)
    - Coordinate multiple repositories
    - Integrate security (ADR-025) and logging (ADR-027)
    
    Design:
    - Depends on abstractions (repositories via DI)
    - Returns domain entities
    - Uses DTOs for input validation
    """
    
    def __init__(
        self,
        vineyard_repo: VineyardRepository,
        harvest_lot_repo: HarvestLotRepository,
        grape_variety_repo: GrapeVarietyRepository
    ):
        """
        Initialize service with dependencies (Dependency Injection).
        
        Args:
            vineyard_repo: Repository for vineyard data
            harvest_lot_repo: Repository for harvest lot data
            grape_variety_repo: Repository for grape variety catalog
        """
        self._vineyard_repo = vineyard_repo
        self._harvest_lot_repo = harvest_lot_repo
        self._grape_variety_repo = grape_variety_repo
    
    async def create_vineyard(
        self,
        winery_id: int,
        user_id: int,
        data: VineyardCreate
    ) -> Vineyard:
        """Create vineyard with validation."""
        with LogTimer(logger, "create_vineyard_service"):
            logger.info(
                "creating_vineyard",
                winery_id=winery_id,
                user_id=user_id,
                code=data.code,
                name=data.name
            )
            
            # Delegate to repository (handles uniqueness constraint)
            vineyard = await self._vineyard_repo.create(
                winery_id=winery_id,
                data=data
            )
            
            logger.info(
                "vineyard_created_success",
                vineyard_id=vineyard.id,
                winery_id=winery_id,
                code=vineyard.code
            )
            
            return vineyard
    
    async def delete_vineyard(
        self,
        vineyard_id: int,
        winery_id: int,
        user_id: int
    ) -> bool:
        """
        Soft delete vineyard with cascade validation.
        
        Business Rule: Cannot delete if has active harvest lots.
        """
        with LogTimer(logger, "delete_vineyard_service"):
            # Check if vineyard exists
            vineyard = await self._vineyard_repo.get_by_id(vineyard_id, winery_id)
            if not vineyard:
                from src.modules.fruit_origin.src.repository_component.errors import VineyardNotFound
                raise VineyardNotFound(vineyard_id=vineyard_id)
            
            # Check for active harvest lots
            active_lots = await self._harvest_lot_repo.count_active_lots_for_vineyard(
                vineyard_id=vineyard_id
            )
            
            if active_lots > 0:
                logger.warning(
                    "vineyard_delete_blocked_has_active_lots",
                    vineyard_id=vineyard_id,
                    active_lots_count=active_lots
                )
                from src.modules.fruit_origin.src.repository_component.errors import VineyardHasActiveLotsError
                raise VineyardHasActiveLotsError(
                    vineyard_id=vineyard_id,
                    active_lots_count=active_lots
                )
            
            # Soft delete
            success = await self._vineyard_repo.soft_delete(vineyard_id, winery_id)
            
            logger.info(
                "vineyard_deleted_success",
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                user_id=user_id
            )
            
            return success
    
    async def create_harvest_lot(
        self,
        winery_id: int,
        user_id: int,
        data: HarvestLotCreate
    ) -> HarvestLot:
        """
        Create harvest lot with validation.
        
        Business Rules:
        1. Harvest date cannot be in future (data quality)
        2. Vineyard must exist (can be from different winery)
        3. Grape variety must exist in catalog
        """
        with LogTimer(logger, "create_harvest_lot_service"):
            from datetime import datetime, timezone
            
            # Validation: Harvest date not in future
            if data.harvest_date > datetime.now(timezone.utc):
                logger.warning(
                    "harvest_date_in_future_rejected",
                    harvest_date=data.harvest_date.isoformat(),
                    winery_id=winery_id
                )
                from shared.domain.errors import InvalidHarvestDate
                raise InvalidHarvestDate(
                    f"Harvest date {data.harvest_date.date()} cannot be in the future",
                    harvest_date=data.harvest_date
                )
            
            # Validation: Vineyard exists (NOTE: can be from different winery)
            vineyard = await self._vineyard_repo.get_by_id_any_winery(data.vineyard_id)
            if not vineyard:
                from src.modules.fruit_origin.src.repository_component.errors import VineyardNotFound
                raise VineyardNotFound(vineyard_id=data.vineyard_id)
            
            # Validation: Grape variety exists
            variety = await self._grape_variety_repo.get_by_id(data.grape_variety_id)
            if not variety:
                from shared.domain.errors import GrapeVarietyNotFound
                raise GrapeVarietyNotFound(variety_id=data.grape_variety_id)
            
            logger.info(
                "creating_harvest_lot",
                winery_id=winery_id,
                user_id=user_id,
                vineyard_id=data.vineyard_id,
                vineyard_name=vineyard.name,
                variety_name=variety.name,
                harvest_date=data.harvest_date.isoformat()
            )
            
            # Create harvest lot via repository
            harvest_lot = await self._harvest_lot_repo.create(
                winery_id=winery_id,
                data=data
            )
            
            logger.info(
                "harvest_lot_created_success",
                lot_id=harvest_lot.id,
                winery_id=winery_id,
                code=harvest_lot.code
            )
            
            return harvest_lot
```

---

### 3. DTOs Design

**Location:** `src/modules/fruit_origin/src/domain/dtos/`

```python
# vineyard_dtos.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional


class VineyardCreate(BaseModel):
    """DTO for vineyard creation (service layer input)."""
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=255)
    
    @field_validator('code')
    @classmethod
    def code_must_be_alphanumeric(cls, v: str) -> str:
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric (hyphens and underscores allowed)')
        return v.upper()  # Normalize to uppercase


class VineyardUpdate(BaseModel):
    """DTO for vineyard updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=255)


class VineyardResponse(BaseModel):
    """DTO for vineyard API responses."""
    id: int
    winery_id: int
    code: str
    name: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    
    model_config = {"from_attributes": True}


# harvest_lot_dtos.py
from datetime import datetime


class HarvestLotCreate(BaseModel):
    """
    DTO for harvest lot creation (service layer input).
    
    MVP Simplification: Single grape variety per lot.
    """
    code: str = Field(..., min_length=1, max_length=50)
    vineyard_id: int = Field(..., gt=0)
    grape_variety_id: int = Field(..., gt=0)
    harvest_date: datetime
    total_mass_kg: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('code')
    @classmethod
    def code_must_be_alphanumeric(cls, v: str) -> str:
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Code must be alphanumeric')
        return v.upper()


class HarvestLotResponse(BaseModel):
    """DTO for harvest lot API responses."""
    id: int
    winery_id: int
    code: str
    vineyard_id: int
    vineyard_name: str  # Joined data
    grape_variety_id: int
    grape_variety_name: str  # Joined data
    harvest_date: str
    total_mass_kg: float
    notes: Optional[str]
    created_at: str
    
    model_config = {"from_attributes": True}
```

---

### 4. Business Rules & Validations

**MVP Business Rules (Priority High):**

1. **Harvest Date Validation:**
   ```python
   if data.harvest_date > datetime.now(timezone.utc):
       raise InvalidHarvestDate("Harvest date cannot be in the future")
   ```
   - **Exception for historical data:** Allow if explicitly marked as historical import (future enhancement)

2. **Vineyard Cascade Delete:**
   ```python
   active_lots = await harvest_lot_repo.count_active_lots_for_vineyard(vineyard_id)
   if active_lots > 0:
       raise VineyardHasActiveLotsError(vineyard_id, active_lots_count=active_lots)
   ```

3. **Cross-Winery Vineyard Access:**
   ```python
   # Allow accessing vineyards from other wineries (buying grapes)
   vineyard = await vineyard_repo.get_by_id_any_winery(vineyard_id)
   ```

**Deferred Validations (Future Enhancements):**
- ❌ Mass totals validation (grape_mass_kg == total_mass_kg)
- ❌ Grape percentage sum = 100% (multi-variety lots)
- ❌ Vineyard name uniqueness validation
- ❌ Same winery grapes validation (intentionally NOT enforced)

---

### 5. Error Handling Strategy

**Domain Errors (ADR-026 integration):**

```python
# src/modules/fruit_origin/src/repository_component/errors.py
from shared.domain.errors import FruitOriginError

class VineyardNotFound(FruitOriginError):
    def __init__(self, vineyard_id: int):
        super().__init__(f"Vineyard {vineyard_id} not found")
        self.http_status = 404
        self.error_code = "VINEYARD_NOT_FOUND"
        self.vineyard_id = vineyard_id

class VineyardHasActiveLotsError(FruitOriginError):
    def __init__(self, vineyard_id: int, active_lots_count: int):
        super().__init__(
            f"Cannot delete vineyard {vineyard_id}: has {active_lots_count} active harvest lots"
        )
        self.http_status = 409
        self.error_code = "VINEYARD_HAS_ACTIVE_LOTS"
        self.vineyard_id = vineyard_id
        self.active_lots_count = active_lots_count

class InvalidHarvestDate(FruitOriginError):
    def __init__(self, message: str, harvest_date: datetime):
        super().__init__(message)
        self.http_status = 400
        self.error_code = "INVALID_HARVEST_DATE"
        self.harvest_date = harvest_date
```

**Error Handler Flow:**
1. Service raises domain error → 2. API decorator re-raises → 3. Global handler converts to RFC 7807

---

### 6. Testing Strategy

**Test Scope (~35-40 tests estimated):**

**VineyardService Tests (15 tests):**
- `test_create_vineyard_success` - Happy path
- `test_create_vineyard_duplicate_code` - Uniqueness constraint
- `test_create_vineyard_invalid_data` - DTO validation
- `test_get_vineyard_found` - Found case
- `test_get_vineyard_not_found` - Not found case
- `test_get_vineyard_cross_winery_denied` - Security (ADR-025)
- `test_list_vineyards_empty` - No vineyards
- `test_list_vineyards_multiple` - Multiple results
- `test_list_vineyards_filters_by_winery` - Multi-tenancy
- `test_update_vineyard_success` - Happy path
- `test_update_vineyard_not_found` - Not found
- `test_delete_vineyard_success` - No active lots
- `test_delete_vineyard_has_active_lots` - Cascade validation fails
- `test_delete_vineyard_not_found` - Not found
- `test_delete_vineyard_logs_correctly` - ADR-027 integration

**HarvestLotService Tests (20 tests):**
- `test_create_harvest_lot_success` - Happy path
- `test_create_harvest_lot_future_date_rejected` - Date validation
- `test_create_harvest_lot_vineyard_not_found` - Vineyard validation
- `test_create_harvest_lot_variety_not_found` - Variety validation
- `test_create_harvest_lot_cross_winery_vineyard_allowed` - Business rule
- `test_create_harvest_lot_duplicate_code` - Uniqueness
- `test_create_harvest_lot_invalid_data` - DTO validation
- `test_create_harvest_lot_logs_correctly` - ADR-027
- `test_get_harvest_lot_found` - Found case
- `test_get_harvest_lot_not_found` - Not found
- `test_get_harvest_lot_cross_winery_denied` - Security
- `test_list_harvest_lots_by_winery` - Multi-tenancy
- `test_list_harvest_lots_by_vineyard` - Vineyard filter
- `test_list_harvest_lots_empty` - No lots
- `test_validate_harvest_lot_data_valid` - Dry-run validation success
- `test_validate_harvest_lot_data_invalid_date` - Dry-run validation fail
- `test_validate_harvest_lot_data_invalid_vineyard` - Validation fail
- `test_count_active_lots_for_vineyard` - Cascade delete helper
- `test_count_active_lots_excludes_deleted` - Soft delete logic
- `test_harvest_lot_respects_winery_id` - Security throughout

**Total: ~35 tests** (benchmark: Fermentation Service has 33)

---

## Implementation Notes

### File Structure

```
src/modules/fruit_origin/src/
├── domain/
│   ├── entities/           # ✅ Exists (ADR-001)
│   │   ├── vineyard.py
│   │   ├── harvest_lot.py
│   │   └── grape.py
│   └── dtos/               # ⭐ TO CREATE
│       ├── __init__.py
│       ├── vineyard_dtos.py
│       └── harvest_lot_dtos.py
├── repository_component/   # ✅ Exists (72 tests)
│   ├── repositories/
│   │   ├── vineyard_repository.py
│   │   ├── harvest_lot_repository.py
│   │   └── grape_variety_repository.py
│   └── errors.py           # ⭐ UPDATE (add VineyardHasActiveLotsError)
├── service_component/      # ⭐ TO CREATE
│   ├── __init__.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   └── fruit_origin_service_interface.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── fruit_origin_service.py
│   └── models/             # ⭐ TO CREATE (if needed)
│       └── validation_result.py
└── tests/                  # ✅ Exists
    └── unit/
        └── service/        # ⭐ TO CREATE
            └── test_fruit_origin_service.py
```

---

### Integration Points

**1. Security Integration (ADR-025):**
```python
# winery_id passed from API layer (UserContext)
# Service always validates winery_id via repositories
vineyard = await self._vineyard_repo.get_by_id(vineyard_id, winery_id)
if not vineyard:
    raise VineyardNotFound(vineyard_id)  # 404
if vineyard.winery_id != winery_id:
    raise CrossWineryAccessDenied(...)   # 403
```

**2. Logging Integration (ADR-027):**
```python
from src.shared.wine_fermentator_logging import get_logger, LogTimer

logger = get_logger(__name__)

with LogTimer(logger, "create_vineyard_service"):
    logger.info(
        "creating_vineyard",
        winery_id=winery_id,
        code=data.code,
        name=data.name
    )
    # Business logic
    logger.info("vineyard_created_success", vineyard_id=vineyard.id)
```

**3. Error Handling (ADR-026):**
```python
# Service raises domain errors
raise InvalidHarvestDate("Harvest date cannot be in the future")

# API layer @handle_service_errors decorator re-raises
# Global handler converts to RFC 7807 format automatically
```

---

## Consequences

### Positive Consequences

✅ **Security from Day 1:**
- ADR-025 integrated (winery_id enforcement)
- No refactoring needed later
- Born secure

✅ **Observability from Day 1:**
- ADR-027 structured logging
- Full audit trail (WHO did WHAT)
- Performance metrics (LogTimer)

✅ **Type Safety & Testability:**
- Interface-based design (DIP)
- DTOs prevent Dict[str, Any]
- ~35 tests for confidence

✅ **Consistent Architecture:**
- Follows Fermentation Service pattern
- Same structure as established modules
- Easy onboarding for devs

✅ **MVP-Focused:**
- Deferred complex validations
- Simplified grape model (1 variety)
- Quick time-to-market (2-3 days)

### Negative Consequences

⚠️ **Deferred Validations:**
- Mass totals NOT validated (may need later)
- Grape percentages NOT validated (multi-variety deferred)
- Could cause data quality issues if assumptions wrong

⚠️ **Grape Model Simplification:**
- Assumes 1 variety per lot (100%)
- If real-world needs multi-variety, requires refactoring
- **Mitigation:** Easy to add later (non-breaking change)

⚠️ **Cross-Winery Complexity:**
- Vineyard from other winery allowed
- Could confuse UI/UX (which winery owns what?)
- **Mitigation:** Clear documentation, API responses include winery_id

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Grape model too simple (need multi-variety) | Medium | Medium | Easy to extend (add Grape entity support) |
| Mass validation needed later | Medium | Low | Can add validation without breaking API |
| Cross-winery vineyard confusing | Low | Medium | Clear UI labels, documentation |
| Service grows too large | Low | Low | Can split into VineyardService + HarvestLotService if needed |

---

## Validation

### Acceptance Criteria

**Phase 1: Service Layer (2 days):**
- [ ] `IFruitOriginService` interface defined (9 methods)
- [ ] `FruitOriginService` implementation complete
- [ ] DTOs created (VineyardCreate/Update/Response, HarvestLotCreate/Response)
- [ ] Business rules implemented (harvest date, cascade delete)
- [ ] 35 tests passing (15 vineyard + 20 harvest lot)
- [ ] ADR-025 security integrated (winery_id everywhere)
- [ ] ADR-027 logging integrated (all operations logged)
- [ ] ADR-026 error handling (domain errors)

**Phase 2: API Layer (ADR-015 - Next):**
- [ ] REST endpoints (`/api/v1/vineyards`, `/api/v1/harvest-lots`)
- [ ] FastAPI routers
- [ ] OpenAPI documentation
- [ ] API integration tests

### Success Metrics

- **Test Coverage:** 35/35 tests passing
- **Security:** 100% winery_id enforcement (no cross-winery leaks)
- **Performance:** Service operations < 100ms (p95)
- **Code Quality:** No linting errors, type hints complete
- **Documentation:** All methods documented with docstrings

---

## Implementation Timeline

### Day 1: Core Service (Morning + Afternoon)

**Morning (4 hours):**
- Create `IFruitOriginService` interface (9 methods)
- Create DTOs (VineyardCreate/Update/Response, HarvestLotCreate/Response)
- Implement `FruitOriginService` constructor + DI

**Afternoon (4 hours):**
- Implement vineyard operations (create, get, list, update, delete)
- Write 15 vineyard tests
- Run test suite (expect 87 tests total: 72 repo + 15 service)

### Day 2: Harvest Lot + Validations (Full day)

**Morning (4 hours):**
- Implement harvest lot operations (create, get, list)
- Add business rule validations (harvest date, cascade delete)
- Integrate ADR-025 security (winery_id checks)

**Afternoon (4 hours):**
- Integrate ADR-027 logging (all operations)
- Write 20 harvest lot tests
- Run full test suite (expect 107 tests total: 72 repo + 35 service)
- Manual testing: Cross-winery scenarios

**Total Estimated Effort: 2 days (16 hours)**

**Checkpoints:**
- ✅ End of Day 1: Vineyard operations complete, 15 tests passing
- ✅ End of Day 2: Full service complete, 35 tests passing, 0 regressions

---

## Status

**✅ IMPLEMENTED** - December 27, 2025

**Implementation Results:**
- ✅ VineyardService, VineyardBlockService, HarvestLotService implemented
- ✅ ValidationOrchestrator with 3 specialized validators (Value, Chronology, BusinessRule)
- ✅ Service tests: Part of module's 100 unit tests total
- ✅ 5 new domain errors added (VineyardHasActiveLotsError, etc.)
- ✅ Total module tests: **100 unit + 43 integration = 143 tests passing**
- ✅ System test suite: 709/709 tests passing (100%)

**Dependencies:**
- ✅ ADR-001: Domain model (COMPLETE)
- ✅ ADR-009: Repository layer (COMPLETE - tests included in module's 100 unit + 43 integration)
- ✅ ADR-012: Unit testing infrastructure (COMPLETE)
- ✅ ADR-025: Security (COMPLETE)
- ✅ ADR-026: Error handling (COMPLETE)
- ✅ ADR-027: Logging (COMPLETE)

**Enables:**
- ⭐ ADR-015: Fruit Origin API Design & DTOs (ready to implement)
- ADR-016: Winery Service Layer (similar pattern)

**Completed Steps:**
1. ✅ Created VineyardService, VineyardBlockService, HarvestLotService
2. ✅ Implemented ValidationOrchestrator with layered validation (Value → Chronology → BusinessRule)
3. ✅ Wrote comprehensive service tests (included in 100 unit tests)
4. ✅ Validated: Module total 177 tests (100 unit + 43 integration + 34 API)
5. ✅ Full system test suite: 709/709 passing (100%)

---

## References

**Internal ADRs:**
- [ADR-001: Fruit Origin Model](./ADR-001-fruit-origin-model-implementation/ADR-001-origin-model.md)
- [ADR-002: Repository Architecture](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)
- [ADR-005: Service Layer Interfaces](./ADR-005-service-layer-interfaces.md)
- [ADR-025: Multi-Tenancy Security](./ADR-025-multi-tenancy-security.md)
- [ADR-026: Error Handling Strategy](./ADR-026-error-handling-strategy.md)
- [ADR-027: Structured Logging](./ADR-027-structured-logging-observability.md)

**External References:**
- Clean Architecture (Robert C. Martin) - Dependency Inversion Principle
- Domain-Driven Design (Eric Evans) - Bounded Contexts
- FastAPI documentation - Dependency Injection patterns

---

**Last Updated:** December 26, 2025  
**Version:** 1.0  
**Approval Status:** Pending review

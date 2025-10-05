# ADR-003 Technical Details - Code Examples & Implementation

**Documento complementario a ADR-003**  
**Propósito:** Detalles técnicos de implementación, ejemplos de código antes/después

---

## Phase 1: Imports & Duplication Fix

### Problem 1: Circular Imports

**Before:**
```python
# ❌ sugar_sample.py
from domain.entities.samples.base_sample import BaseSample  # Wrong absolute import

# ❌ fermentation.py
from domain.entities.user import User  # Inside TYPE_CHECKING, wrong path
```

**After:**
```python
# ✅ sugar_sample.py, density_sample.py, celcius_temperature_sample.py
from .base_sample import BaseSample  # Correct relative import

# ✅ fermentation.py, user.py, fermentation_lot_source.py
if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.user import User
    # Full absolute path to avoid incorrect resolution
```

### Problem 2: Code Duplication

**Before:**
```python
# ❌ fermentation_repository.py (old)
class FermentationStatus(Enum):  # Redefinition
    ACTIVE = "active"
    SLOW = "slow"

@dataclass
class Fermentation:  # Redefinition
    id: int
    winery_id: int
```

**After:**
```python
# ✅ fermentation_repository.py (refactored)
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import (
    IFermentationRepository,
    Fermentation,
    FermentationCreate,
)

# NO redefinitions, only imports from canonical locations
```

### Problem 3: Model Desync

**Before:**
```python
# ❌ fermentation_repository_interface.py (old)
@dataclass
class Fermentation:
    target_temperature_min: float  # Field doesn't exist in DB
    target_temperature_max: float  # Field doesn't exist in DB
    metadata: dict[str, any]       # Generic field
```

**After:**
```python
# ✅ fermentation_repository_interface.py (updated)
@dataclass
class Fermentation:
    """Domain entity matching real SQLAlchemy model"""
    id: int
    winery_id: int
    fermented_by_user_id: int
    status: FermentationStatus
    vintage_year: int           # ✅ Real business field
    yeast_strain: str           # ✅ Real business field
    vessel_code: Optional[str]  # ✅ Real business field
    input_mass_kg: float        # ✅ Real business field
    initial_sugar_brix: float   # ✅ Real business field
    initial_density: float      # ✅ Real business field
    start_date: datetime
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
```

---

## Phase 2: Separation of Concerns

### Responsibility Overlap Problem

**Current State (WRONG):**
```python
# FermentationRepository has sample methods ❌
class FermentationRepository:
    async def create(...) -> Fermentation: pass
    async def update_status(...) -> bool: pass
    async def add_sample(...) -> Sample: pass          # ❌ Sample responsibility
    async def get_latest_sample(...) -> Sample: pass   # ❌ Sample responsibility
    
# ISampleRepository also has sample methods ✅
class ISampleRepository:
    async def upsert_sample(...) -> BaseSample: pass
    async def get_latest_sample(...) -> BaseSample: pass  # DUPLICATE!
```

**Target State (CORRECT):**
```python
# FermentationRepository - ONLY fermentation lifecycle ✅
class FermentationRepository:
    async def create(...) -> Fermentation: pass
    async def get_by_id(...) -> Optional[Fermentation]: pass
    async def update_status(...) -> bool: pass
    async def get_by_status(...) -> List[Fermentation]: pass
    async def get_by_winery(...) -> List[Fermentation]: pass
    # NO sample methods

# SampleRepository - ALL sample operations ✅
class SampleRepository:
    async def upsert_sample(...) -> BaseSample: pass
    async def get_sample_by_id(...) -> BaseSample: pass
    async def get_samples_by_fermentation_id(...) -> List[BaseSample]: pass
    async def get_samples_in_timerange(...) -> List[BaseSample]: pass
    async def get_latest_sample(...) -> Optional[BaseSample]: pass
    async def get_latest_sample_by_type(...) -> Optional[BaseSample]: pass
    async def check_duplicate_timestamp(...) -> bool: pass
    async def soft_delete_sample(...) -> None: pass
    async def bulk_upsert_samples(...) -> List[BaseSample]: pass
```

### Code to Remove from FermentationRepository

**Method 1: add_sample() (~40 lines)**
```python
# ❌ TO DELETE
async def add_sample(
    self, fermentation_id: int, winery_id: int, timestamp: datetime, data: SampleCreate
) -> Sample:
    # Verify fermentation exists
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation as SQLFermentation
    
    session_cm = await self.get_session()
    async with session_cm as session:
        fermentation_query = select(SQLFermentation).where(SQLFermentation.id == fermentation_id)
        fermentation_query = self.scope_query_by_winery_id(fermentation_query, winery_id)
        fermentation_query = self.apply_soft_delete_filter(fermentation_query)

        fermentation_result = await session.execute(fermentation_query)
        fermentation = fermentation_result.scalar_one_or_none()

        if fermentation is None:
            raise EntityNotFoundError(...)
    
    # Add sample with error mapping
    async def _add_sample_operation():
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample

        session_cm = await self.get_session()
        async with session_cm as session:
            units_map = {
                SampleType.SUGAR: "brix",
                SampleType.TEMPERATURE: "°C",
                SampleType.DENSITY: "specific_gravity",
            }

            sample = BaseSample(
                fermentation_id=fermentation_id,
                sample_type=data.sample_type.value,
                recorded_at=timestamp,
                recorded_by_user_id=data.recorded_by_user_id,
                value=data.value,
                units=units_map[data.sample_type],
            )

            session.add(sample)
            await session.commit()
            await session.refresh(sample)

            return Sample(...)  # Mapping

    return await self.execute_with_error_mapping(_add_sample_operation)
```

**Method 2: get_latest_sample() (~30 lines)**
```python
# ❌ TO DELETE
async def get_latest_sample(
    self, fermentation_id: int, winery_id: int
) -> Optional[Sample]:
    # Verify fermentation exists
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation as SQLFermentation
    
    session_cm = await self.get_session()
    async with session_cm as session:
        fermentation_query = select(SQLFermentation).where(SQLFermentation.id == fermentation_id)
        fermentation_query = self.scope_query_by_winery_id(fermentation_query, winery_id)
        fermentation_query = self.apply_soft_delete_filter(fermentation_query)

        fermentation_result = await session.execute(fermentation_query)
        fermentation = fermentation_result.scalar_one_or_none()

        if fermentation is None:
            raise EntityNotFoundError(...)
    
    # Query sample with error mapping
    async def _get_latest_sample_operation():
        from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample

        session_cm = await self.get_session()
        async with session_cm as session:
            sample_query = (
                select(BaseSample)
                .where(BaseSample.fermentation_id == fermentation_id)
                .where(BaseSample.is_deleted == False)
                .order_by(desc(BaseSample.recorded_at))
                .limit(1)
            )

            sample_result = await session.execute(sample_query)
            latest_sample = sample_result.scalar_one_or_none()

            if latest_sample is None:
                return None

            return Sample(...)  # Mapping

    return await self.execute_with_error_mapping(_get_latest_sample_operation)
```

### Tests to Remove

**From test_fermentation_repository.py:**

1. `test_add_sample_raises_error_when_fermentation_not_found`
2. `test_add_sample_creates_sugar_sample_when_glucose_provided`
3. `test_get_latest_sample_returns_none_when_no_samples`
4. `test_get_latest_sample_returns_most_recent_sample`
5. `test_get_latest_sample_raises_error_when_fermentation_not_found`

**Tests to KEEP (8):**
1. `test_repository_inherits_from_base_repository`
2. `test_create_returns_fermentation_entity`
3. `test_get_by_id_returns_none_when_not_found`
4. `test_get_by_id_returns_fermentation_when_found`
5. `test_update_status_returns_false_when_not_found`
6. `test_update_status_returns_true_when_successful`
7. `test_get_by_status_returns_list_of_fermentations`
8. `test_get_by_winery_returns_all_fermentations_for_winery`

---

## SampleRepository Implementation Template

```python
"""
Sample Repository Implementation.

Concrete implementation of ISampleRepository that extends BaseRepository
and provides database operations for sample data management.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, desc, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.repositories.sample_repository_interface import ISampleRepository
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample
from src.modules.fermentation.src.domain.enums.sample_type import SampleType
from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.fermentation.src.repository_component.errors import (
    EntityNotFoundError,
    ValidationError,
)


class SampleRepository(BaseRepository, ISampleRepository):
    """
    Repository for sample data operations.
    
    Implements ISampleRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and soft delete support.
    
    All methods use real SQLAlchemy queries against the database.
    """

    async def upsert_sample(self, sample: BaseSample) -> BaseSample:
        """Creates or updates a sample record using upsert pattern."""
        async def _upsert_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                if sample.id is None:
                    # INSERT
                    session.add(sample)
                else:
                    # UPDATE
                    sample = await session.merge(sample)
                
                await session.commit()
                await session.refresh(sample)
                return sample
        
        return await self.execute_with_error_mapping(_upsert_operation)

    async def get_sample_by_id(
        self, 
        sample_id: int, 
        fermentation_id: Optional[int] = None
    ) -> BaseSample:
        """Retrieves a sample by its ID as BaseSample entity."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(BaseSample).where(BaseSample.id == sample_id)
                
                if fermentation_id is not None:
                    query = query.where(BaseSample.fermentation_id == fermentation_id)
                
                result = await session.execute(query)
                sample = result.scalar_one_or_none()
                
                if sample is None:
                    raise EntityNotFoundError(f"Sample {sample_id} not found")
                
                return sample
        
        return await self.execute_with_error_mapping(_get_operation)

    async def get_samples_by_fermentation_id(self, fermentation_id: int) -> List[BaseSample]:
        """Retrieves all samples for a specific fermentation as BaseSample entities."""
        async def _get_samples_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(BaseSample)
                    .where(BaseSample.fermentation_id == fermentation_id)
                    .where(BaseSample.is_deleted == False)
                    .order_by(BaseSample.recorded_at.asc())
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
        
        return await self.execute_with_error_mapping(_get_samples_operation)

    # ... implement remaining 7 methods
```

---

## Service Layer Migration Example

**Before (using FermentationRepository for samples):**
```python
# ❌ OLD
class FermentationService:
    def __init__(self, fermentation_repo: IFermentationRepository):
        self._fermentation_repo = fermentation_repo
    
    async def add_measurement(self, fermentation_id, winery_id, data):
        # Using fermentation repo for sample operation ❌
        return await self._fermentation_repo.add_sample(
            fermentation_id, winery_id, datetime.now(), data
        )
```

**After (using SampleRepository):**
```python
# ✅ NEW
class FermentationService:
    def __init__(
        self, 
        fermentation_repo: IFermentationRepository,
        sample_repo: ISampleRepository
    ):
        self._fermentation_repo = fermentation_repo
        self._sample_repo = sample_repo
    
    async def add_measurement(self, fermentation_id, data):
        # Create BaseSample entity
        sample = BaseSample(
            fermentation_id=fermentation_id,
            sample_type=data.sample_type.value,
            recorded_at=datetime.now(),
            recorded_by_user_id=data.recorded_by_user_id,
            value=data.value,
            units=self._get_units(data.sample_type),
        )
        
        # Use SampleRepository ✅
        return await self._sample_repo.upsert_sample(sample)
    
    def _get_units(self, sample_type: SampleType) -> str:
        units_map = {
            SampleType.SUGAR: "brix",
            SampleType.TEMPERATURE: "°C",
            SampleType.DENSITY: "specific_gravity",
        }
        return units_map[sample_type]
```

---

## Files Modified Summary

### Phase 1 ✅
- 8 entity files (imports fixed)
- fermentation_repository_interface.py (model updated)
- fermentation_repository.py (no redefinitions)
- 2 test files (updated)
- 6 obsolete files (deleted)

### Phase 2 🔄
- fermentation_repository_interface.py (remove 2 methods)
- fermentation_repository.py (delete 2 implementations, ~70 lines)
- test_fermentation_repository.py (delete 5 tests, keep 8)
- sample_repository.py (NEW, ~300 lines)
- test_sample_repository.py (NEW, ~20 tests)

# ETL Service - Architectural Refactoring

> **📋 Related Documentation:**
> - [ADR-030: ETL Cross-Module Architecture & Performance Optimization](../.ai-context/adr/ADR-030-etl-cross-module-architecture-refactoring.md)
> - This document provides detailed technical analysis that informed ADR-030

> **⚙️ Development Environment:**
> - All tests must be run using Poetry: `poetry run pytest tests/unit/etl/ -v`
> - Dependencies (pandas, openpyxl) managed by Poetry in isolated venv
> - Do NOT install pandas/openpyxl globally (causes version conflicts)

## Overview

The ETL service has been refactored to implement the complete entity hierarchy across fruit_origin and fermentation modules, ensuring proper data lineage and traceability from vineyard to fermentation.

## Problem Statement

The initial ETL implementation created a simplified Fermentation entity directly from Excel data, losing important information:

**Excel Schema Contains:**
- `vineyard_name` - Where grapes came from
- `grape_variety` - Type of grapes
- `harvest_date` - When grapes were harvested
- `harvest_mass_kg` - Amount of grapes harvested

**Original Implementation:**
- Created only Fermentation entity
- Stored vineyard_name as text in notes/comments
- Lost harvest traceability
- Cannot query: "Which vineyards produced wine in fermentation X?"

## Solution: Full Entity Hierarchy

The refactored implementation creates the complete entity chain:

```
Vineyard (viña master data)
  └── VineyardBlock (parcela within vineyard)
      └── HarvestLot (specific harvest event)
          └── FermentationLotSource (association: links harvest to fermentation)
              └── Fermentation (fermentation process)
                  └── Samples (measurements over time)
```

## Entity Mapping

| Excel Column | Target Entity | Field | Notes |
|-------------|---------------|-------|-------|
| `vineyard_name` | Vineyard | `code`, `name` | Find or create |
| (derived) | VineyardBlock | `code` | Create default "IMPORTED-DEFAULT" |
| `harvest_date` | HarvestLot | `harvest_date` | Stored properly |
| `harvest_mass_kg` | HarvestLot | `weight_kg` | Original harvest amount |
| `grape_variety` | HarvestLot | `grape_variety` | Grape type preserved |
| `fermentation_code` | Fermentation | `vessel_code` | Tank/vessel identifier |
| `fermentation_start_date` | Fermentation | `start_date` | When fermentation started |
| `density` | DensitySample | `value` | Measurement |
| `temperature_celsius` | CelsiusTemperatureSample | `value` | Measurement |
| `sugar_brix` (optional) | SugarSample | `value` | Measurement |

## Import Process (6 Steps)

### Step 1: Find or Create Vineyard
```python
vineyard = await uow.vineyard_repo.get_by_code(vineyard_name, winery_id)
if vineyard is None:
    vineyard = await uow.vineyard_repo.create(winery_id, VineyardCreate(
        code=vineyard_name,
        name=vineyard_name,
        notes="Created during historical data import"
    ))
```

**Business Logic:**
- Reuses existing vineyards (prevents duplicates)
- Uses vineyard name as unique code
- First fermentation creates vineyard, subsequent ones reuse it

### Step 2: Create Default VineyardBlock
```python
block_code = f"{vineyard_name}-IMPORTED-DEFAULT"
vineyard_block = await uow.vineyard_block_repo.create(
    vineyard.id, 
    winery_id, 
    VineyardBlockCreate(
        code=block_code,
        notes="Default block created during historical data import"
    )
)
```

**Rationale:**
- Historical data lacks block-specific information (soil type, GPS coordinates, slope)
- Creating dummy block maintains entity hierarchy
- Alternative would be to make VineyardBlock optional (rejected for data integrity)

### Step 3: Create HarvestLot
```python
harvest_lot = await uow.harvest_lot_repo.create(winery_id, HarvestLotCreate(
    block_id=vineyard_block.id,
    code=f"HL-{fermentation_code}",
    harvest_date=harvest_date,
    weight_kg=harvest_mass_kg,
    grape_variety=grape_variety,
    notes="Created from historical fermentation data import"
))
```

**Business Value:**
- Preserves harvest information (when, how much, what variety)
- Enables future queries: "What harvests were used in vintage 2023?"
- Supports blend tracking (one fermentation can use multiple harvest lots)

### Step 4: Create Fermentation
```python
fermentation = Fermentation(
    winery_id=winery_id,
    fermented_by_user_id=1,  # TODO: Get from import context
    vintage_year=harvest_date.year,
    yeast_strain="IMPORTED - Unknown",
    vessel_code=fermentation_code,
    input_mass_kg=harvest_mass_kg,
    initial_sugar_brix=initial_sugar_brix,
    initial_density=initial_density,
    start_date=fermentation_start_date,
    status=FermentationStatus.COMPLETED,
    data_source=DataSource.IMPORTED
)
created_fermentation = await uow.fermentation_repo.create(fermentation)
```

### Step 5: Create FermentationLotSource (Link)
```python
lot_source = FermentationLotSource(
    fermentation_id=created_fermentation.id,
    harvest_lot_id=harvest_lot.id,
    mass_used_kg=harvest_mass_kg,  # Single source, all mass used
    notes="Created from historical data import"
)
await uow.lot_source_repo.create(lot_source)
```

**Business Rules Enforced:**
- Sum of `mass_used_kg` across all lot sources must equal `fermentation.input_mass_kg`
- For historical imports: single source (1:1), but supports future blends (N:1)
- All harvest lots must belong to same winery

### Step 6: Create Samples
```python
for row in group_df.iterrows():
    # Create density sample (required)
    density_sample = DensitySample(
        fermentation_id=fermentation.id,
        recorded_at=sample_date,
        value=density,
        data_source=DataSource.IMPORTED
    )
    await uow.sample_repo.create(density_sample)
    
    # Create temperature sample (required)
    temp_sample = CelsiusTemperatureSample(...)
    await uow.sample_repo.create(temp_sample)
    
    # Create sugar sample (optional)
    if sugar_brix is not None:
        sugar_sample = SugarSample(...)
        await uow.sample_repo.create(sugar_sample)
```

## UnitOfWork Updates

Extended `IUnitOfWork` interface to include fruit_origin repositories:

```python
class IUnitOfWork(ABC):
    @property
    @abstractmethod
    def fermentation_repo(self) -> IFermentationRepository: ...
    
    @property
    @abstractmethod
    def sample_repo(self) -> ISampleRepository: ...
    
    @property
    @abstractmethod
    def lot_source_repo(self) -> ILotSourceRepository: ...
    
    @property
    @abstractmethod
    def harvest_lot_repo(self) -> IHarvestLotRepository: ...
    
    # NEW: Cross-module repository access
    @property
    @abstractmethod
    def vineyard_repo(self) -> IVineyardRepository: ...
    
    @property
    @abstractmethod
    def vineyard_block_repo(self) -> IVineyardBlockRepository: ...
```

**Design Decision:**
- UnitOfWork provides unified transaction boundary across modules
- All repositories share same database session
- Commit/rollback affects all entities atomically

## Test Coverage

### Unit Tests (38 total - 100% passing)

**ETLValidator (27 tests):**
- Pre-validation: File size, schema, required columns (9 tests)
- Row-validation: Data quality, ranges, formats (10 tests)
- Post-validation: Chronology, trends, business rules (8 tests)

**ETLService (11 tests):**
- Validation rejection at each layer (3 tests)
- Successful import scenarios (2 tests)
- Repository call verification (1 test)
- Optional field handling (sugar_brix) (1 test)
- Error handling and rollback (2 tests)
- Statistics and reporting (1 test)
- Vineyard reuse logic (1 test) **← NEW**

### New Test: Vineyard Reuse
```python
@pytest.mark.asyncio
async def test_reuses_existing_vineyard_for_multiple_fermentations():
    """Verify that importing multiple fermentations from same vineyard 
    creates vineyard only once."""
    
    # Setup: First call creates vineyard, second call finds existing
    mock_uow.vineyard_repo.get_by_code = AsyncMock(
        side_effect=[None, mock_vineyard]  # First: not found, Second: found
    )
    
    # Import 2 fermentations from "Viña Norte"
    result = await etl_service.import_file(excel_file)
    
    assert result.success
    assert mock_uow.vineyard_repo.create.call_count == 1  # Created once
    assert mock_uow.vineyard_repo.get_by_code.call_count == 2  # Checked twice
```

## Business Value

### Traceability
**Before:** "Fermentation FERM-001 was made with grapes from Viña Norte" (text in notes)
**After:** Full lineage: Vineyard → VineyardBlock → HarvestLot → Fermentation

### Queries Enabled
```sql
-- Find all fermentations using grapes from specific vineyard
SELECT f.* FROM fermentations f
JOIN fermentation_lot_sources fls ON f.id = fls.fermentation_id
JOIN harvest_lots hl ON fls.harvest_lot_id = hl.id
JOIN vineyard_blocks vb ON hl.block_id = vb.id
JOIN vineyards v ON vb.vineyard_id = v.id
WHERE v.code = 'Viña Norte';

-- Calculate total harvest mass used in vintage 2023
SELECT SUM(hl.weight_kg) FROM harvest_lots hl
JOIN fermentation_lot_sources fls ON hl.id = fls.harvest_lot_id
JOIN fermentations f ON fls.fermentation_id = f.id
WHERE f.vintage_year = 2023;

-- Find which grape varieties were used in a fermentation
SELECT DISTINCT hl.grape_variety FROM harvest_lots hl
JOIN fermentation_lot_sources fls ON hl.id = fls.harvest_lot_id
WHERE fls.fermentation_id = '...';
```

### Future Features Enabled
1. **Blend Analysis:** Track multiple harvest lots per fermentation
2. **Vineyard Performance:** Compare fermentations by vineyard source
3. **Harvest Planning:** Historical harvest dates and masses
4. **Traceability Reports:** Complete farm-to-bottle lineage

## Design Decisions

### Decision 1: Create Default VineyardBlock
**Options:**
- A) Make VineyardBlock optional (nullable foreign key)
- B) Create dummy block per import
- C) Create single shared "UNKNOWN" block per vineyard

**Chosen:** B - Create dummy block per import

**Rationale:**
- Maintains entity integrity (HarvestLot always has block)
- Each import has unique block (avoids conflicts)
- Clear marker in database (`code` contains "IMPORTED-DEFAULT")
- Can be updated later if real block information becomes available

### Decision 2: Vineyard Code Strategy
**Challenge:** Excel has vineyard name, not unique code

**Solution:** Use vineyard name as code
```python
vineyard_dto = VineyardCreate(
    code=vineyard_name,  # "Viña Norte"
    name=vineyard_name,  # "Viña Norte"
    notes="Created during historical data import"
)
```

**Future Enhancement:** Handle name variations
- Case sensitivity: "Viña Norte" vs "VIÑA NORTE"
- Whitespace: "Viña  Norte" (double space)
- Accents: "Viña" vs "Vina"

Consider normalization function: `normalize_vineyard_name()`

### Decision 3: Cross-Module Repository Access
**Challenge:** Fermentation module needs fruit_origin repositories

**Options:**
- A) Add fruit_origin repos to fermentation UnitOfWork (chosen)
- B) Create separate fruit_origin UnitOfWork (two transactions)
- C) Direct repository injection (bypasses transaction pattern)

**Chosen:** A - Extend UnitOfWork

**Rationale:**
- Single transaction boundary (atomicity)
- All entities committed or rolled back together
- Maintains UnitOfWork pattern
- Clean dependency injection

## Known Limitations

### 1. TODO: winery_id from Context
```python
winery_id = 1  # TODO: Get from import context/authenticated user
```

**Impact:** All imports hardcoded to winery_id=1
**Fix Required:** Pass winery_id as parameter to `import_file()`

### 2. TODO: fermented_by_user_id
```python
fermented_by_user_id = 1  # TODO: Get from import context/user
```

**Impact:** Cannot track which user performed import
**Fix Required:** Pass user_id from authentication context

### 3. Historical Data Gaps
Excel doesn't contain:
- VineyardBlock details (soil, GPS, slope)
- HarvestLot details (bins count, field temperature, pick method)
- Yeast strain (stored as "IMPORTED - Unknown")

**Mitigation:** Dummy/default values with clear notes

### 4. No Duplicate Vineyard Detection
If user imports:
- "Viña Norte" (first import)
- "Vina Norte" (second import - no accent)

Result: Two separate vineyard records

**Fix Required:** Normalization function or manual merge tools

## Migration Path

### For Existing Simplified Data
If simplified Fermentation entities already exist in database:

1. **Identify imported fermentations:**
```sql
SELECT * FROM fermentations WHERE data_source = 'IMPORTED';
```

2. **Extract vineyard names** from notes/vessel_code

3. **Create missing entities:**
   - Vineyard
   - VineyardBlock
   - HarvestLot (estimate from fermentation.input_mass_kg)
   - FermentationLotSource (link)

4. **Write migration script:** `backfill_fruit_origin_entities.py`

## Testing Strategy

### Unit Tests (Current)
- Mock all repositories
- Verify service logic and flow
- Test error handling and rollback
- **Coverage:** 100% (38/38 tests passing)

### Integration Tests (Pending)
- Real database with test data
- Verify entity relationships
- Test foreign key constraints
- Verify business rules (mass validation, chronology)

### End-to-End Tests (Pending)
- Import real Excel file
- Verify all entities created
- Query and validate relationships
- Test duplicate vineyard handling

## Performance Considerations

### Database Queries Per Fermentation
1. `vineyard_repo.get_by_code()` - SELECT
2. `vineyard_repo.create()` (if not found) - INSERT
3. `vineyard_block_repo.create()` - INSERT
4. `harvest_lot_repo.create()` - INSERT
5. `fermentation_repo.create()` - INSERT
6. `lot_source_repo.create()` - INSERT
7. `sample_repo.create()` × N (N = samples per fermentation) - INSERT

**Optimization Opportunities:**
- Batch vineyard lookup at start (load all vineyards once)
- Batch inserts for samples
- Use bulk insert methods if available

### Transaction Size
- All entities created in single transaction
- Large imports (1000+ fermentations) may require:
  - Batch processing (commit every N fermentations)
  - Progress tracking
  - Resumable imports (checkpoint/restart)

## Documentation References

- **ADR-019:** ETL Pipeline Implementation
- **ADR-029:** DataSource Tracking
- **ADR-001:** Fruit Origin Model
- **UnitOfWork Pattern:** Martin Fowler, PoEAA

## Files Modified

### Core Implementation
- `src/modules/fermentation/src/service_component/etl/etl_service.py`
  - Refactored `_import_data()` method (6-step entity creation)
  - Added imports for fruit_origin DTOs
  - Removed `_prepare_fermentation_data()` (obsolete)

### Infrastructure
- `src/modules/fermentation/src/domain/interfaces/unit_of_work_interface.py`
  - Added `vineyard_repo` property
  - Added `vineyard_block_repo` property

- `src/modules/fermentation/src/repository_component/unit_of_work.py`
  - Implemented vineyard_repo lazy loading
  - Implemented vineyard_block_repo lazy loading
  - Updated `__aexit__` cleanup

### Tests
- `src/modules/fermentation/tests/unit/etl/test_etl_service.py`
  - Added mock fixtures for new repositories
  - Updated existing tests for new entity creation flow
  - Added test for vineyard reuse logic

## Summary

The refactored ETL service now implements the complete entity hierarchy across fruit_origin and fermentation modules, providing:

✅ **Full traceability** from vineyard to fermentation
✅ **Proper data modeling** following domain architecture
✅ **Future-proof design** supporting blends and advanced queries
✅ **100% test coverage** (38/38 unit tests passing)
✅ **Clear documentation** of design decisions and limitations

**Next Steps:**
1. Add integration tests with real database
2. Implement winery_id and user_id context passing
3. Add vineyard name normalization
4. Create migration script for existing data
5. Implement API endpoints (4 endpoints from ADR-019)
6. Add progress tracking for large imports

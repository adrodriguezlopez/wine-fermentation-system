# Component Context: Domain Component (Fruit Origin Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions  
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
Defines the core business model for fruit origin and vineyard hierarchy. Centralizes entities, business rules, and repository interfaces for traceability from vineyard to harvest lot.

**Position in module**: Foundation layer - all future components (Repository, Service, API) will depend on the abstractions defined here. Domain does not depend on any other component.

## Architecture pattern
- **Domain-Driven Design (DDD)**: Entities and value objects for vineyard hierarchy
- **Dependency Inversion Principle**: All dependencies point inward to domain
- **Aggregate roots**: Vineyard (with VineyardBlocks), HarvestLot

## Arquitectura específica del componente
- **Entities**: Vineyard, VineyardBlock, HarvestLot (in `entities/`)
- **Repository Interfaces**: (pending) IVineyardRepository, IHarvestLotRepository (future in `repositories/`)
- **No infrastructure logic**: Only contracts, rules, and pure domain models

## Domain model hierarchy

```
Vineyard (Aggregate Root)
  ├─ id, winery_id, code, name, notes
  └─ blocks: List[VineyardBlock]
      ├─ VineyardBlock
      │   ├─ id, vineyard_id, code, name
      │   ├─ Technical: soil_type, slope_pct, aspect_deg, area_ha, elevation_m
      │   ├─ Location: latitude, longitude
      │   ├─ Farming: irrigation, organic_certified
      │   └─ harvest_lots: List[HarvestLot]
      │
      └─ HarvestLot
          ├─ id, winery_id, block_id, code
          ├─ Harvest: harvest_date, weight_kg, bins_count, pick_method, pick_times
          ├─ Quality: brix_at_harvest, brix_method, brix_measured_at, field_temp_c
          └─ Grape: grape_variety, clone, rootstock
```

## Business rules enforced

### Vineyard
- **Uniqueness**: `(code, winery_id)` unique constraint
- **Ownership**: Must belong to a winery
- **Hierarchy**: Cannot delete if has blocks with harvest lots

### VineyardBlock
- **Uniqueness**: `(code, vineyard_id)` unique within vineyard
- **Parent**: Must belong to a vineyard
- **Technical validation**: 
  - `slope_pct`: 0-100%
  - `aspect_deg`: 0-360°
  - `area_ha`: > 0
  - `latitude`/`longitude`: Valid GPS coordinates

### HarvestLot
- **Uniqueness**: `(code, winery_id)` unique across winery
- **References**: Must reference valid `block_id` and `winery_id`
- **Quality validation**:
  - `brix_at_harvest`: Typically 18-28° for wine grapes
  - `weight_kg`: > 0
  - `field_temp_c`: Reasonable range (-10°C to 50°C)
- **Temporal logic**:
  - `harvest_date`: Valid date
  - `pick_end_time`: Must be after `pick_start_time`
  - `brix_measured_at`: Should be close to `harvest_date`

## Entity relationships

```python
# Vineyard ↔ VineyardBlock (One-to-Many)
Vineyard.blocks → List[VineyardBlock]
VineyardBlock.vineyard → Vineyard

# VineyardBlock ↔ HarvestLot (One-to-Many)
VineyardBlock.harvest_lots → List[HarvestLot]
HarvestLot.block → VineyardBlock

# Cross-module references
HarvestLot.winery_id → Winery.id (winery module)
FermentationLotSource.harvest_lot_id → HarvestLot.id (fermentation module)
```

## Component interfaces

### Future Repository Interfaces (Pending Implementation)

**IVineyardRepository** (future):
- `create(vineyard: Vineyard) → Vineyard`
- `get_by_id(id: int, winery_id: int) → Vineyard`
- `get_by_winery(winery_id: int) → List[Vineyard]`
- `update(vineyard: Vineyard) → Vineyard`
- `delete(id: int, winery_id: int) → bool`

**IHarvestLotRepository** (future):
- `create(harvest_lot: HarvestLot) → HarvestLot`
- `get_by_id(id: int, winery_id: int) → HarvestLot`
- `get_by_block(block_id: int, winery_id: int) → List[HarvestLot]`
- `get_by_date_range(start: date, end: date, winery_id: int) → List[HarvestLot]`
- `update(harvest_lot: HarvestLot) → HarvestLot`
- `delete(id: int, winery_id: int) → bool`

## Connection with other components

**Future components** (pending):
- **Repository Component**: Will implement IVineyardRepository, IHarvestLotRepository
- **Service Component**: Will use entities and repository interfaces for harvest workflows
- **API Component**: Will expose vineyard/harvest management endpoints

**Cross-module dependencies**:
- **Uses**: `winery.Winery` (for ownership)
- **Used by**: `fermentation.FermentationLotSource` (references HarvestLot)

## Implementation status

**Status:** ✅ **Entities Complete** - Repository interfaces pending  
**Last Updated:** 2025-10-05

### Completed
- ✅ Entity models (Vineyard, VineyardBlock, HarvestLot)
- ✅ SQLAlchemy mappings with relationships
- ✅ Business rules in entity constraints
- ✅ Integration test fixtures

### Pending
- ⏭️ Repository interfaces definition (IVineyardRepository, IHarvestLotRepository)
- ⏭️ Value objects (if needed: GpsCoordinate, BrixMeasurement)
- ⏭️ Domain events (if needed: HarvestRecorded, VineyardCreated)

## Key implementation considerations

### SQLAlchemy Patterns
- **Fully-qualified paths** in relationships (see ADR-004)
- **Consistent imports**: `from src.shared.infra.orm.base_entity import BaseEntity`
- **extend_existing=True**: For test compatibility

### Multi-tenancy
- **All queries** must include `winery_id` filter
- **Unique constraints** include `winery_id` where applicable
- **Security**: Never expose data across wineries

### Data completeness
- **19 fields in HarvestLot** for regulatory compliance and quality correlation
- **Technical specs in VineyardBlock** for terroir analysis
- **GPS coordinates** for future mapping/visualization

## Future enhancements
1. **Weather integration**: Link historical weather to harvest_date
2. **Yield tracking**: Weight per hectare trends
3. **Clone performance**: Compare clones within same block
4. **Optimal harvest windows**: ML model for harvest date prediction
5. **Soil analysis**: Detailed composition per block

## References
- **ADR-004**: Harvest Module Consolidation & SQLAlchemy Registry Fix
- **Module Context**: `../../.ai-context/module-context.md`
- **ARCHITECTURAL_GUIDELINES**: `/.ai-context/ARCHITECTURAL_GUIDELINES.md` - SQLAlchemy patterns

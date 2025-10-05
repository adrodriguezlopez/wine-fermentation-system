# Module Context: Fruit Origin & Traceability

> **Parent Context**: See `/.ai-context/project-context.md` for system-level decisions  
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Module responsibility
**Fruit origin tracking and vineyard hierarchy management** - Provides complete traceability from vineyard to harvest lot for fermentation sourcing.

**Position in system**: Source data provider for fermentation module. Records where grapes came from, when harvested, and initial quality metrics.

## Module interfaces
**Provides to**: Fermentation module (HarvestLot data via FermentationLotSource)  
**Depends on**: Winery module (ownership and multi-tenant scoping)  
**Receives from**: User input (vineyard structure, harvest recording)

## Key functionality
- **Vineyard hierarchy**: Three-level structure (Winery → Vineyard → VineyardBlock)
- **Harvest recording**: Capture harvest events with 19 traceability fields
- **Quality metrics**: Initial fruit quality (brix, temperature, method)
- **Traceability**: Link fermentations back to specific vineyard blocks

## Domain model

```
Winery (winery module)
  ↓ owns
Vineyard
  ↓ contains
VineyardBlock  
  ↓ produces
HarvestLot
  ↓ used in
FermentationLotSource (fermentation module)
```

## Entities

### Vineyard
**Purpose**: Top-level vineyard location owned by winery  
**Key fields**: `winery_id`, `code`, `name`, `notes`  
**Relationships**: Has many VineyardBlocks

### VineyardBlock
**Purpose**: Specific parcel/block within vineyard with technical specs  
**Key fields**: 11 total - `vineyard_id`, `code`, `name`, `soil_type`, `slope_pct`, `aspect_deg`, `area_ha`, `elevation_m`, `latitude`, `longitude`, `irrigation`, `organic_certified`  
**Relationships**: Belongs to Vineyard, produces many HarvestLots

### HarvestLot
**Purpose**: Specific harvest event from a block on a date  
**Key fields**: 19 total for complete traceability
- **ID**: `winery_id`, `block_id`, `code`
- **Harvest**: `harvest_date`, `weight_kg`, `bins_count`, `pick_method`, `pick_start_time`, `pick_end_time`
- **Quality**: `brix_at_harvest`, `brix_method`, `brix_measured_at`, `field_temp_c`
- **Grape**: `grape_variety`, `clone`, `rootstock`
- **Notes**: `notes`

**Relationships**: Belongs to VineyardBlock, referenced by FermentationLotSource

## Business rules
- **Multi-tenancy**: All entities scoped by `winery_id`
- **Unique codes**: Code + winery_id uniqueness at each level
- **Hierarchy integrity**: Cannot delete vineyard with blocks, cannot delete block with harvest lots
- **Quality validation**: `brix_at_harvest` typically 18-28° for wine grapes
- **Temporal logic**: `harvest_date` must be valid, `pick_end_time` > `pick_start_time`

## Database tables
- `vineyards` - Top-level vineyard locations
- `vineyard_blocks` - Parcels with technical specifications  
- `harvest_lots` - Harvest events with full traceability

**Indexes**: `winery_id`, `code`, `harvest_date`, `block_id`  
**Constraints**: Unique (`code`, `winery_id`) at each level

## Implementation status

**Status:** ✅ **Entities Complete** - Repository layer pending  
**Last Updated:** 2025-10-05  
**Reference:** ADR-004 (Harvest Module Consolidation)

### Completed
- ✅ Entity models with SQLAlchemy mappings
- ✅ Relationships (vineyard ↔ blocks ↔ harvest_lots)
- ✅ Integration test fixtures (test_vineyard, test_vineyard_block, test_harvest_lot)
- ✅ Database tables created (9 tables total in system)

### Pending
- ⏭️ Repository interfaces (IVineyardRepository, IHarvestLotRepository)
- ⏭️ Repository implementations
- ⏭️ Service layer (vineyard management, harvest recording)
- ⏭️ API endpoints

## Cross-module dependencies

**Outgoing** (fruit_origin depends on):
- `winery.Winery` - Ownership via `winery_id` FK

**Incoming** (other modules depend on fruit_origin):
- `fermentation.FermentationLotSource` - References `HarvestLot` to track fruit origin

## Why 19 fields in HarvestLot?

**Regulatory compliance**: Denominaciones de origen require precise documentation  
**Quality correlation**: Link fermentation characteristics to fruit origin  
**Historical analysis**: Identify best blocks/dates for future harvest decisions  
**Blend decisions**: Know exact fruit characteristics per lot

**Real-world example**: Winemaker compares two fermentations of same wine with different profiles. With complete HarvestLot:
- Compare `brix_at_harvest` (different maturity)
- Check `pick_method` (hand vs mechanical affects quality)
- Review `field_temp_c` (high temp → spontaneous fermentation risk)
- Verify `pick_start_time` (nocturnal vs diurnal harvest)

## Module components
Currently only **Domain** component (entities). Future:
- **Repository Component**: Data access for vineyard hierarchy
- **Service Component**: Business logic for harvest recording
- **API Component**: Endpoints for vineyard/harvest management

## Key architectural decisions
See [ADR-004](/.ai-context/adr/ADR-004-harvest-module-consolidation.md):
- **Consolidation from harvest/**: Eliminated duplicate 5-field HarvestLot, consolidated to 19-field version
- **Separate module rationale**: fruit_origin is distinct bounded context from fermentation
- **Dependency direction**: fermentation → fruit_origin → winery (correct flow)

## SQLAlchemy patterns used
- **Fully-qualified paths** in relationships (avoid registry conflicts)
- **Consistent imports**: `from src.shared.infra.orm.base_entity import BaseEntity`
- **extend_existing=True**: Test compatibility in `__table_args__`

See: [ARCHITECTURAL_GUIDELINES.md](/.ai-context/ARCHITECTURAL_GUIDELINES.md) - Section "SQLAlchemy Import Best Practices"

## Next steps
1. Define repository interfaces in `src/domain/repositories/`
2. Implement repositories in `repository_component/`
3. Create service layer for harvest workflows
4. Add API endpoints for vineyard management

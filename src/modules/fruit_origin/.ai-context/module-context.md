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

**Status:** ✅ **Fully Complete — Domain, Repository, Service, API**
**Last Updated:** April 2026

| Component | Tests |
|-----------|-------|
| Domain entities (Vineyard, VineyardBlock, HarvestLot) | Covered via integration |
| Repository Layer (3 repos, ADR-012 pattern) | ~70 unit tests |
| Service Layer (FruitOriginService + ETL orchestration) | ~50 unit tests |
| API Layer (11 endpoints: 6 vineyard + 5 harvest-lot) | 34 API tests |
| Integration Tests | 43 tests |
| **Total** | **~150+ passing** |

### Test execution
```powershell
cd src/modules/fruit_origin
python -m pytest tests/ -v
```

## Module components
- ✅ **Domain Component**: Entities (Vineyard, VineyardBlock, HarvestLot) with SQLAlchemy mappings
- ✅ **Repository Component**: Data access for vineyard hierarchy and harvest lots
- ✅ **Service Component**: Business logic for harvest recording and vineyard management
- ✅ **API Component**: REST endpoints for vineyard and harvest lot management (ADR-015 ✅)

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
- 🔮 VineyardBlock API endpoints (future phase)
- 🔮 Advanced filtering/search endpoints

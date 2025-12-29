# Component Context: Repository Component (Fruit Origin Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence and retrieval operations** for vineyard hierarchy and harvest lot entities within the Fruit Origin Module.

**Position in module**: Foundation layer providing data access abstraction to Service Component, enforcing multi-tenant isolation and referential integrity at persistence level.

**Architectural Decision:** Following ADR-009 (Missing Repositories) and ADR-012 (Unit Testing Phase 3), this component implements strict separation with VineyardRepository, VineyardBlockRepository, and HarvestLotRepository handling their respective entity lifecycles.

## Architecture pattern
**Repository Pattern** with dependency injection and transaction coordination.

**Design approach**: Abstract data access through domain interfaces with PostgreSQL-specific implementations optimized for vineyard hierarchy and harvest traceability patterns.

- **Repository Interfaces**: Not defined here. IVineyardRepository, IVineyardBlockRepository, IHarvestLotRepository are defined in domain component and shared across Service and Repository components.
- **Concrete Repositories**: VineyardRepository, VineyardBlockRepository, HarvestLotRepository (SQLAlchemy implementations)
- **Entity Models**: Vineyard, VineyardBlock, HarvestLot with SQLAlchemy mappings
- **Data flow**: Service → Repository Interface → Concrete Repository → SQLAlchemy → PostgreSQL
- **Extension points**: Geospatial queries, harvest analytics, bulk import operations
- **Integration strategy**: Dependency injection provides implementations to Service Component

## Component interfaces

### **Receives from (Service Component)**
- Entity creation/update requests: Validated vineyard/block/harvest data ready for persistence
- Query requests: Filtering by winery, vineyard, block, harvest date with pagination
- Transaction coordination: Multi-repository operations for hierarchy integrity

### **Provides to (Service Component)**
- Entity instances: Vineyard, VineyardBlock, HarvestLot objects with relationships loaded
- Query results: Paginated collections with metadata
- Operation confirmations: Success/failure status with conflict information

### **Uses (Database Layer)**
- SQLAlchemy ORM: Entity mapping and relationship management
- PostgreSQL connection: ACID transactions and concurrent access
- Connection pooling: Performance optimization for concurrent operations

## Key patterns implemented
- **Repository Pattern**: Abstract persistence concerns from business logic
- **Multi-tenant Security**: All queries automatically filtered by winery_id
- **Soft Deletes**: Maintain audit trail while allowing logical deletion
- **Async/Await**: Non-blocking database operations with AsyncSession
- **Query Optimization**: Indexed lookups on winery_id, code, harvest_date
- **Shared Infrastructure**: BaseRepository patterns from ADR-012

## Business rules enforced
- **Multi-tenant isolation**: All queries scoped by winery_id (security boundary)
- **Unique codes**: Code + winery_id uniqueness at each hierarchy level
- **Referential integrity**: Vineyard→Block→HarvestLot relationships with FK constraints
- **Soft delete filtering**: All queries exclude records where deleted_at IS NOT NULL
- **Hierarchy protection**: Cannot delete vineyard with active blocks, block with active harvest lots

## Connection with other components
**Service Component**: Receives repository interfaces via dependency injection
**Domain Component**: Implements repository interfaces, uses entity models
**Database Layer**: Direct SQLAlchemy ORM integration with PostgreSQL

## Implementation status

**Status:** ✅ **Repository Layer Complete with Integration Tests**  
**Last Updated:** December 29, 2025  
**Reference:** ADR-009 (Missing Repositories), ADR-012 (Unit Testing Phase 3)

**Note:** This component is production-ready for service layer usage. Service layer integration complete (ADR-014). Tests for repository layer are included in the module's unit and integration test totals.

### Implemented Components

**VineyardRepository** ✅ COMPLETE
- **Methods:** 7 (create, get_by_id, get_by_code, list_by_winery, update, delete, exists_by_code)
- **Tests:** Repository tests included in module's 100 unit + 43 integration totals
- **Status:** Fully implemented with SQLAlchemy integration, multi-tenancy verified
- **Compliance:** ADR-012 migrated (shared test infrastructure)

**VineyardBlockRepository** ✅ COMPLETE
- **Methods:** 7 (create, get_by_id, get_by_code, list_by_vineyard, update, delete, exists_by_code)
- **Tests:** Repository tests included in module's 100 unit + 43 integration totals
- **Status:** Fully implemented with relationship handling
- **Compliance:** ADR-012 migrated (shared test infrastructure)

**HarvestLotRepository** ✅ COMPLETE
- **Methods:** 8 (create, get_by_id, get_by_code, list_by_block, list_by_winery, update, delete, exists_by_code)
- **Tests:** Repository tests included in module's 100 unit + 43 integration totals (includes chronological sorting, temporal queries)
- **Status:** Fully implemented with temporal query optimization
- **Compliance:** ADR-012 migrated (shared test infrastructure)

## Database schema
**Tables:**
- `vineyards`: Top-level vineyard locations (4 fields + timestamps + soft delete)
- `vineyard_blocks`: Parcels with technical specs (11 fields + timestamps + soft delete)
- `harvest_lots`: Harvest events with traceability (19 fields + timestamps + soft delete)

**Indexes:**
- `winery_id`: Multi-tenant filtering (all tables)
- `code`: Unique code lookups (all tables)
- `harvest_date`: Temporal queries (harvest_lots)
- `block_id`: Relationship navigation (harvest_lots)

**Constraints:**
- Unique: (code, winery_id) at each level
- Foreign Keys: block_id → vineyard_id, harvest_lot → block_id (CASCADE on delete)

## Next steps
None - Repository layer complete ✅

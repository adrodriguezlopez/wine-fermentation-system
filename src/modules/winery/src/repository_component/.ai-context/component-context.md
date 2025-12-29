# Component Context: Repository Component (Winery Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence and retrieval operations** for winery entities within the Winery Module.

**Position in module**: Foundation layer providing data access abstraction to Service Component (future), enforcing winery code uniqueness at persistence level.

**Architectural Decision:** Following ADR-009 (Missing Repositories) and ADR-012 (Unit Testing Phase 3), this component implements the root entity repository with WineryRepository handling winery lifecycle and serving as the multi-tenancy foundation for the entire system.

## Architecture pattern
**Repository Pattern** with dependency injection and async PostgreSQL.

**Design approach**: Abstract data access through IWineryRepository interface with PostgreSQL-specific implementations optimized for winery identity and multi-tenancy lookups.

- **Repository Interface**: Not defined here. IWineryRepository is defined in domain component and shared across Service and Repository components.
- **Concrete Repository**: WineryRepository (SQLAlchemy implementation)
- **Entity Model**: Winery with SQLAlchemy mappings (root entity, no parent relationships)
- **Data flow**: Service → Repository Interface → Concrete Repository → SQLAlchemy → PostgreSQL
- **Extension points**: Legal entity management, branding, multi-location support
- **Integration strategy**: Dependency injection provides implementation to Service Component

## Component interfaces

### **Receives from (Service Component - future)**
- Entity creation/update requests: Validated winery data ready for persistence
- Query requests: Lookup by ID, code, list all wineries
- Transaction coordination: Single-repository operations (no multi-tenant filtering needed)

### **Provides to (Service Component - future)**
- Entity instances: Winery objects with complete data
- Query results: Collections with metadata
- Operation confirmations: Success/failure status with conflict information

### **Uses (Database Layer)**
- SQLAlchemy ORM: Entity mapping and relationship management
- PostgreSQL connection: ACID transactions and concurrent access
- Connection pooling: Performance optimization for concurrent operations

## Key patterns implemented
- **Repository Pattern**: Abstract persistence concerns from business logic
- **Root Entity**: No multi-tenant filtering (Winery is the root, not scoped by another entity)
- **Global Uniqueness**: Code uniqueness enforced across all wineries
- **Soft Deletes**: Maintain audit trail while allowing logical deletion
- **Async/Await**: Non-blocking database operations with AsyncSession
- **Shared Infrastructure**: BaseRepository patterns from ADR-012

## Business rules enforced
- **Global code uniqueness**: Code must be unique across all wineries (no scoping)
- **Required fields**: Code and name are mandatory
- **Code format**: Uppercase alphanumeric with hyphens (e.g., "BODEGA-001")
- **Soft delete filtering**: All queries exclude records where deleted_at IS NOT NULL
- **Referential integrity**: Winery is referenced by Vineyard, Fermentation, HarvestLot (other modules)
- **Deletion protection**: Cannot hard-delete winery with active data in other modules

## Connection with other components
**Service Component (future)**: Receives IWineryRepository implementation via dependency injection
**Domain Component**: Implements IWineryRepository interface, uses Winery entity
**Database Layer**: Direct SQLAlchemy ORM integration with PostgreSQL

## Implementation status

**Status:** ✅ **Repository Layer Complete with Integration Tests**  
**Last Updated:** December 29, 2025  
**Reference:** ADR-009 (Missing Repositories), ADR-012 (Unit Testing Phase 3)

**Note:** This component is production-ready for service layer usage. Service layer implementation is next phase.

### Implemented Components

**WineryRepository** ✅ COMPLETE
- **Methods:** 8 (create, get_by_id, get_by_code, list_all, update, delete, exists_by_code, count)
- **Unit Tests:** 22 passing (100% coverage of interface)
- **Integration Tests:** 18 passing (real PostgreSQL operations)
- **Status:** Fully implemented with SQLAlchemy integration
- **Compliance:** ADR-012 migrated (shared test infrastructure)
- **Recent Fix (Dec 29, 2025):** Added `aiosqlite = "^0.21.0"` to pyproject.toml dev-dependencies to fix integration test failures

**Method Details:**
- ✅ `create(winery: Winery) -> Winery` - Create with duplicate code checking
- ✅ `get_by_id(winery_id: int) -> Optional[Winery]` - Retrieve by ID (excludes deleted)
- ✅ `get_by_code(code: str) -> Optional[Winery]` - Retrieve by code (excludes deleted)
- ✅ `list_all() -> List[Winery]` - List all active wineries
- ✅ `update(winery: Winery) -> Winery` - Update with timestamp management
- ✅ `delete(winery_id: int) -> bool` - Soft delete (sets deleted_at)
- ✅ `exists_by_code(code: str) -> bool` - Check code uniqueness
- ✅ `count() -> int` - Count active wineries

## Database schema
**Table:** `wineries`

**Fields:**
- `id`: Primary key (serial)
- `code`: Unique identifier (varchar, indexed, unique)
- `name`: Winery name (varchar, required)
- `location`: Optional location (varchar)
- `notes`: Optional notes (text)
- `created_at`: Timestamp (auto)
- `updated_at`: Timestamp (auto)
- `deleted_at`: Soft delete timestamp (nullable)

**Indexes:**
- `code`: Unique index for fast lookups and uniqueness constraint

**Constraints:**
- Unique: `code` (global uniqueness, no scoping)
- NOT NULL: `code`, `name`

## Next steps
Service layer implementation (WineryService with CRUD operations)

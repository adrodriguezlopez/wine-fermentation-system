# Component Context: Repository Component (Fermentation Management Module)

> **Parent Context**: See `../module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Data persistence and retrieval operations** for fermentation and sample entities within the Fermentation Management Module.

**Position in module**: Foundation layer providing data access abstraction to Service Component, enforcing user isolation and referential integrity at persistence level.

**Architectural Decision:** Following ADR-003, this component implements strict separation of concerns with FermentationRepository handling only fermentation lifecycle and SampleRepository handling all sample operations.

## Architecture pattern
**Repository Pattern** with dependency injection and transaction coordination.

**Design approach**: Abstract data access through interfaces with PostgreSQL-specific implementations optimized for time-series fermentation data patterns.

- **Repository Interfaces**: Not defined here. IFermentationRepository, ISampleRepository, and any other repository contracts are defined in the domain component and shared across Service and Repository components.
- **Concrete Repositories**: FermentationRepository, SampleRepository (SQLAlchemy implementations, implement domain interfaces only in this component)
- **Entity Models**: Fermentation, BaseSample with polymorphic inheritance for sample types
- **Data flow**: Service → Repository Interface → Concrete Repository → SQLAlchemy → PostgreSQL
- **Extension points**: Additional repository interfaces, query optimization, caching integration
- **Integration strategy**: Dependency injection provides implementations to Service Component

## Component interfaces

### **Receives from (Service Component)**
- Entity creation/update requests: Validated data ready for persistence
- Query requests: Filtering, pagination, and sorting parameters
- Transaction coordination: Multi-repository operations requiring consistency

### **Provides to (Service Component)**
- Entity instances: Fermentation and sample objects with relationships loaded
- Query results: Paginated collections with metadata
- Operation confirmations: Success/failure status with conflict information

### **Uses (Database Layer)**
- SQLAlchemy ORM: Entity mapping and relationship management
- PostgreSQL connection: ACID transactions and concurrent access
- Connection pooling: Performance optimization for concurrent operations

## Key patterns implemented
- **Repository Pattern**: Abstract persistence concerns from business logic
- **Unit of Work**: Transaction coordination across multiple entities
- **Query Object**: Complex filtering and sorting operations
- **Specification Pattern**: Reusable query conditions for common operations

## Business rules enforced
- **User data isolation**: All queries automatically filter by user context
- **Referential integrity**: Fermentation-sample relationships and constraint enforcement
- **Duplicate detection**: Conflict resolution for sample timestamps and batch operations
- **Soft deletes**: Maintain audit trail while allowing logical deletion

## Connection with other components
**Service Component**: Receives repository interfaces via dependency injection
**Database Layer**: Direct SQLAlchemy ORM integration with PostgreSQL

## Implementation status

**Status:** ✅ **COMPLETE - All Repositories Implemented & Tested**  
**Last Updated:** 2025-10-26  
**Reference:** ADR-003 (Repository Separation), ADR-002 (Repository Architecture)

### Implemented Components

**FermentationRepository** ✅ COMPLETE
- **Methods:** 5 (create, get_by_id, update_status, get_by_status, get_by_winery)
- **Tests:** 8 passing (100% coverage of interface)
- **Status:** Fully implemented with SQLAlchemy integration
- **Compliance:** ADR-003 compliant (zero sample operations)

**SampleRepository** ✅ COMPLETE
- **Methods:** 11 fully implemented
  - ✅ `create()` - Polymorphic sample creation
  - ✅ `upsert_sample()` - Upsert with conflict resolution
  - ✅ `get_sample_by_id()` - Single sample retrieval
  - ✅ `get_samples_by_fermentation_id()` - Chronological listing
  - ✅ `get_samples_in_timerange()` - Time-based queries
  - ✅ `get_latest_sample()` - Most recent sample retrieval
  - ✅ `get_latest_sample_by_type()` - Type-filtered latest sample
  - ✅ `get_fermentation_start_date()` - Helper for validation
  - ✅ `check_duplicate_timestamp()` - Duplicate detection
  - ✅ `soft_delete_sample()` - Logical deletion
  - ✅ `bulk_upsert_samples()` - Batch operations
- **Tests:** 12 passing (interface validation)
- **Status:** Fully implemented with polymorphic support and helper method `_map_to_domain()`
- **Compliance:** ADR-003 compliant (all sample operations centralized)

**Error Handling** ✅ COMPLETE
- **Classes:** 7 error types (RepositoryError hierarchy)
- **Tests:** 19 passing (error chaining, messages, inheritance)
- **Status:** Complete error mapping infrastructure

### Test Coverage
- **Total:** 39 tests passing (100% repository layer coverage)
- **FermentationRepository:** 8 tests (lifecycle operations)
- **SampleRepository:** 12 tests (all methods validated)
- **Error Classes:** 19 tests (error hierarchy and handling)

### Critical Fix Applied (2025-10-26)
**SQLAlchemy Mapper Error Resolution:**
- **Problem:** Double import of sample entities causing mapper registration conflicts
- **Solution:** Moved entity imports inside methods to prevent duplicate registration
- **Impact:** +39 tests enabled (previously blocked)
- **Files Fixed:** 
  - `sample_repository.py` - Removed module-level imports
  - `test_sample_repository.py` - Removed unnecessary imports

### Next Steps (Future Enhancements)
1. **Integration tests** with real PostgreSQL database (Docker-based)
2. **Performance optimization** for time-series queries (indexing strategy)
3. **Query caching** for frequently accessed data
4. **Batch operation improvements** for bulk sample imports
5. **Transaction coordination** for complex multi-repository operations

## Key implementation considerations
- **Async operations**: All methods async for FastAPI compatibility and performance
- **Query optimization**: Time-series queries require indexing strategy for chronological access
- **Transaction management**: Coordinate sample additions with potential analysis triggers
- **Error handling**: Distinguish between constraint violations and system errors
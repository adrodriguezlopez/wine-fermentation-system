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

 **Status:** ✅ **Repository Layer Complete with Integration Tests**  
**Last Updated:** 2025-11-04  
**Reference:** ADR-003 (Repository Separation), ADR-002 (Repository Architecture)

**Note:** This component is production-ready for service layer usage. API layer integration is pending at module level.

### Implemented Components

**FermentationRepository** ✅ COMPLETE
- **Methods:** 6 (create, get_by_id, update_status, get_by_status, get_by_winery, list_by_data_source)
  - ADR-029: `list_by_data_source(winery_id, data_source, include_deleted)` implementado
- **Unit Tests:** 16 passing (8 base + 8 ADR-029)
- **Integration Tests:** 8 passing (real PostgreSQL operations)
- **Status:** Fully implemented with SQLAlchemy integration, multi-tenancy verified
- **Compliance:** ADR-003 compliant (zero sample operations)

**SampleRepository** ✅ COMPLETE + REFACTORED
- **Methods:** 12 fully implemented with async session management
  - ✅ `create()` - Polymorphic sample creation with session context
  - ✅ `upsert_sample()` - Upsert with conflict resolution
  - ✅ `get_sample_by_id()` - Single sample retrieval (returns None if not found)
  - ✅ `get_samples_by_fermentation_id()` - Chronological listing across all types
  - ✅ `get_samples_in_timerange()` - Time-based queries with session context
  - ✅ `get_latest_sample()` - Most recent sample retrieval
  - ✅ `get_latest_sample_by_type()` - Type-filtered latest sample with session context
  - ✅ `get_fermentation_start_date()` - Helper for validation with session context
  - ✅ `check_duplicate_timestamp()` - Duplicate detection with session context
  - ✅ `soft_delete_sample()` - Logical deletion with session context (no error if not found)
  - ✅ `bulk_upsert_samples()` - Batch operations
  - ✅ `list_by_data_source()` - Filter by data source (ADR-029)
- **Unit Tests:** 12 passing (interface validation)
- **Integration Tests:** 1 passing (real database persistence)
- **API Integration Tests:** 12 passing (full endpoint validation)
- **Status:** Production-ready with session context managers, error handling, and API integration
- **Compliance:** ADR-003 compliant (all sample operations centralized)
- **ADR-029 Implementation (2026-01-02):**
  - Added `list_by_data_source(fermentation_id, data_source, winery_id)` method
  - Queries across all sample types (SugarSample, DensitySample, CelsiusTemperatureSample)
  - Multi-tenant security via fermentation join
  - Structured logging with ADR-027
- **Recent Refactoring (2025-11-15):**
  - Added `async with session_cm as session:` pattern to all methods
  - Changed ValueError → None returns for not-found scenarios
  - Fixed celcius/celsius typo in imports (6 occurrences)
  - Handle sample_type as both string and enum
  - Fixed SugarSample units override (only default if not provided)
  - File size reduced 24% (608→460 lines) by removing duplicates

**Error Handling** ✅ COMPLETE
- **Classes:** 7 error types (RepositoryError hierarchy)
- **Tests:** 19 passing (error chaining, messages, inheritance)
- **Status:** Complete error mapping infrastructure

### Test Coverage
- **Unit Tests:** 47 passing (repository layer coverage)
  - FermentationRepository: 16 tests (8 base + 8 ADR-029)
  - SampleRepository: 12 tests (all methods validated)
  - Error Classes: 19 tests (error hierarchy and handling)
- **Integration Tests:** 9 passing (real PostgreSQL operations)
  - FermentationRepository: 8 tests (CRUD, multi-tenancy, queries)
  - SampleRepository: 1 test (polymorphic sample persistence)
- **API Integration Tests:** 12 passing (Sample endpoints end-to-end)
  - POST /samples: 4 tests (create, validation, auth, not found)
  - GET /samples: 3 tests (list, empty, not found)
  - GET /samples/{id}: 2 tests (get, not found)
  - GET /samples/latest: 3 tests (latest, no samples, filter by type)
- **Interface Tests:** 2 passing (ADR-029)
  - test_fermentation_repository_interface.py
  - test_sample_repository_interface.py
- **Total:** 70 tests (47 unit + 9 integration + 12 API + 2 interface)

### Critical Fixes Applied

**2025-11-15: Sample Repository Session Management & API Integration**
- **Problem:** Repository methods missing session context, causing "session not defined" errors
- **Solution:** Added `async with session_cm as session:` to all repository methods
- **Impact:** All 12 API integration tests now passing
- **Methods Fixed:**
  - `get_latest_sample_by_type()` - Added session context
  - `check_duplicate_timestamp()` - Added session context
  - `get_fermentation_start_date()` - Added session context
  - `soft_delete_sample()` - Added session context
- **Additional Fixes:**
  - Fixed import typo: `celsius_temperature_sample` → `celcius_temperature_sample`
  - Changed error handling: `ValueError` → `return None` for not-found scenarios
  - Fixed sample_type comparisons to handle both string and enum values
  - Fixed `SugarSample.__init__()` to preserve user-provided units
  - Removed duplicate method implementations (24% file size reduction)

**2025-10-26: SQLAlchemy Mapper Error Resolution**
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
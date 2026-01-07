# Architecture Decision Records (ADRs) - Index

**Wine Fermentation System**  
**Last Update:** December 30, 2025

---

## 📋 ADR Summary

| ADR | Title | Status | Date | Impact |
|-----|-------|--------|------|--------|
| **[ADR-001](./ADR-001-fruit-origin-model-implementation/ADR-001-origin-model.md)** | Fruit Origin Model | ✅ Implemented | 2025-09-25 | High |
| **[ADR-002](./ADR-002-repositories-architecture/ADR-002-repositories-architecture.md)** | Repository Architecture | ✅ Implemented | 2025-09-25 | High |
| **[ADR-003](./ADR-003-repository-interface-refactoring.md)** | Repository Separation of Concerns | ✅ Implemented | 2025-10-04 | Medium |
| **[ADR-004](./ADR-004-harvest-module-consolidation.md)** | Harvest Module Consolidation | ✅ Implemented | 2025-10-05 | High |
| **[ADR-005](./ADR-005-service-layer-interfaces.md)** | Service Layer Interfaces & Type Safety | ✅ Implemented | 2025-10-11 | High |
| **[ADR-006](./ADR-006-api-layer-design.md)** | API Layer Design & FastAPI Integration | ✅ Implemented | 2025-11-15 | High |
| **[ADR-007](./ADR-007-auth-module-design.md)** | Authentication Module (Shared Infrastructure) | ✅ Implemented | 2025-11-04 | Critical |
| **[ADR-008](./ADR-008-centralized-error-handling.md)** | Centralized Error Handling for API Layer | ✅ Implemented | 2025-11-15 | Medium |
| **[ADR-009](./ADR-009-missing-repositories-implementation.md)** | Missing Repositories Implementation | ✅ Implemented | 2025-11-25 | High |
| **[ADR-011](./ADR-011-integration-test-infrastructure-refactoring.md)** | Integration Test Infrastructure Refactoring | ✅ Implemented | 2025-12-13 | High |
| **[ADR-012](./ADR-012-unit-test-infrastructure-refactoring.md)** | Unit Test Infrastructure Refactoring | ✅ Implemented | 2025-12-15 | High |
| **[ADR-014](./ADR-014-fruit-origin-service-layer.md)** | Fruit Origin Service Layer Architecture | ✅ Implemented | 2025-12-27 | High |
| **[ADR-015](./ADR-015-fruit-origin-api-design.md)** | Fruit Origin API Design & REST Endpoints | ✅ Implemented | 2025-12-29 | High |
| **[ADR-016](./ADR-016-winery-service-layer.md)** | Winery Service Layer Architecture | ✅ Implemented | 2025-12-29 | High |
| **[ADR-027](./ADR-027-structured-logging-observability.md)** | Structured Logging & Observability Infrastructure | ✅ Implemented | 2025-12-16 | Critical |
| **[ADR-028](./ADR-028-module-dependency-management.md)** | Module Dependency Management Standardization | ✅ Implemented | 2025-12-23 | Medium |
| **[ADR-029](./ADR-029-data-source-field-historical-tracking.md)** | Data Source Field for Historical Data Tracking | ✅ Implemented | 2026-01-02 | Medium |
| **[ADR-019](./ADR-019-etl-pipeline-historical-data.md)** | ETL Pipeline Design for Historical Data | ✅ Approved | 2025-12-30 | High |
| **[ADR-030](./ADR-030-etl-cross-module-architecture-refactoring.md)** | ETL Cross-Module Architecture & Performance | ✅ Accepted | 2026-01-06 | High |

**Legend:**
- ✅ **Implemented** - Fully implemented with tests passing
- 🚀 **Ready** - Prerequisites met, ready for implementation
- 🔄 **In Progress** - Implementation ongoing
- 📋 **Proposed** - Under review, not yet approved
- ⚠️ **Superseded** - Replaced by newer decision

---

## 📚 Quick Reference

### ADR-001: Fruit Origin Model
**Decision:** Hierarchy Winery → Vineyard → VineyardBlock → HarvestLot  
**Status:** ✅ Implemented  
**Impact:** Enables full traceability from wine to vineyard  
**Key Points:**
- Multi-tenancy prepared (MVP single-tenant)
- Business rules enforced (mass totals, same winery)
- `FermentationLotSource` association table

### ADR-002: Repository Architecture
**Decision:** Ports & Adapters with BaseRepository helper  
**Status:** ✅ Implemented (110 tests passing)  
**Impact:** Foundation for all data access  
**Key Points:**
- Interface-based design (DIP)
- Multi-tenancy scoping
- Error mapping (DB → Domain)
- Soft-delete support

### ADR-003: Repository Separation of Concerns
**Decision:** FermentationRepository ≠ SampleRepository  
**Status:** ✅ Implemented (102 tests passing)  
**Impact:** SRP compliance, cleaner architecture  
**Key Points:**
- Removed samples logic from FermentationRepository
- Fixed circular imports
- Eliminated code duplication
- One repository = one aggregate root

### ADR-004: Harvest Module Consolidation
**Decision:** Consolidate `harvest/` into `fruit_origin/`  
**Status:** ✅ Implemented  
**Impact:** Cleaner bounded context, no duplication  
**Key Points:**
- Eliminated duplicate HarvestLot entity
- SQLAlchemy registry fix (fully-qualified paths)
- Unidirectional relationships with inheritance
- flush() vs commit() in tests

### ADR-005: Service Layer Interfaces & Type Safety
**Decision:** Type-safe service interfaces, DTOs → Entities  
**Status:** ✅ Implemented (115 tests passing)  
**Impact:** Type safety, Clean Architecture, SOLID  
**Key Points:**
- FermentationService: 7 methods (33 tests)
- SampleService: 6 methods (27 tests)
- FermentationValidator extracted (SRP)
- Multi-tenancy enforced
- NO more Dict[str, Any]

### ADR-006: API Layer Design & FastAPI Integration
**Decision:** REST API with FastAPI, JWT auth, Pydantic DTOs  
**Status:** ✅ **FULLY IMPLEMENTED** (Nov 15, 2025)  
**Impact:** Exposes fermentation functionality via HTTP  
**Key Points:**
- **All Phases Complete**: All 18 endpoints implemented (100%)
  - 10 fermentation endpoints (create, get, list, update, delete, validate, timeline, stats, etc.)
  - 8 sample endpoints (create, get, list, latest, types, timerange, validate, delete)
- **Tests**: 90 API tests passing (100% coverage)
- Real PostgreSQL database integration ✅
- JWT authentication with shared Auth module ✅
- Multi-tenancy enforcement (winery_id filtering) ✅
- Pydantic v2 for request/response DTOs ✅
- **Centralized error handling** with decorator pattern ✅
- **Code quality**: ~410 lines eliminated via refactoring ✅
- **Branch**: feature/fermentation-api-layer (merged to main)

### ADR-007: Authentication Module (Shared Infrastructure)
**Decision:** JWT-based auth in src/shared/auth/ with User entity, role-based authorization  
**Status:** ✅ **Implemented & Production Ready** (Nov 4, 2025 | Fixed Nov 15, 2025)  
**Impact:** Unblocks all API layers, enforces multi-tenancy  

### ADR-008: Centralized Error Handling for API Layer
**Decision:** Use decorator pattern for exception→HTTP mapping  
**Status:** ✅ **Implemented** (Nov 15, 2025)  
**Impact:** Eliminated code duplication, improved maintainability  
**Key Points:**
- **Single decorator**: `@handle_service_errors` wraps all endpoints
- **Code reduction**: ~410 lines of duplicated try/except blocks eliminated
- **Standardized mappings**: NotFoundError→404, ValidationError→422, DuplicateError→409, etc.
- **Refactored**: 17/17 endpoints (100%)
- **Tests**: All 90 API tests passing with new error handling
- **Benefits**: DRY principle, single source of truth, easier maintenance

### ADR-009: Missing Repositories Implementation
**Decision:** Implement 5 missing repositories with full test coverage  
**Status:** ✅ **Implemented** (Dec 13, 2025)  
**Impact:** Complete repository layer coverage  
**Key Points:**
- **WineryRepository**: 22 unit + 18 integration tests ✅
- **VineyardRepository**: 28 unit + 11 integration tests ✅
- **VineyardBlockRepository**: 31 unit + 12 integration tests ✅
- **HarvestLotRepository**: 13 unit + 20 integration tests ✅
- **FermentationNoteRepository**: 19 unit + 20 integration tests ✅
- **Total**: 194 new tests (113 unit + 81 integration)
- Multi-tenant security patterns
- Soft-delete support
- Error handling (DuplicateNameError, EntityNotFoundError)

### ADR-011: Integration Test Infrastructure Refactoring
**Decision:** Create shared testing infrastructure, fix SQLAlchemy metadata conflicts  
**Status:** ✅ **Implemented & Fully Resolved** (Dec 13, 2025 | Updated Dec 30, 2025)  
**Impact:** Massive code reduction, metadata blocker eliminated  
**Key Points:**
- **Phase 1**: Shared utilities created (641 lines, 52/52 tests passing) ✅
- **Phase 2**: 3 modules migrated (winery, fruit_origin, fermentation) ✅
- **Phase 3**: **Fermentation integration tests RESOLVED** (Dec 30, 2025) ✅
- **Code reduction**: 635 lines eliminated (79% reduction)
  - Winery: 172 → 23 lines (87% reduction)
  - Fruit Origin: 255 → 49 lines (81% reduction)
  - Fermentation: 375 → 95 lines (75% reduction)
- **Metadata fix**: Function-scoped db_engine resolves "index already exists" errors ✅
- **SessionWrapper pattern**: Savepoint-based transaction management for UnitOfWork tests ✅
- **Validation**: **797/797 tests passing** system-wide (100%) ✅
- **Fermentation Integration**: 49/49 tests passing, included in main suite ✅
- **Components**: TestSessionManager, IntegrationTestConfig, create_integration_fixtures(), EntityBuilder, SessionWrapper
- **Previous limitation RESOLVED**: Sample models now work with isolated fixtures in repository_component/conftest.py

### ADR-012: Unit Test Infrastructure Refactoring
**Decision:** Create shared unit test utilities with builder pattern  
**Status:** ✅ **Implemented - Phase 3 Complete** (Dec 15, 2025)  
**Impact:** 800-1,000 lines eliminated, 50% faster test creation  
**Key Points:**
- **Phase 1**: Core utilities created (86 tests, 4 components) ✅
- **Phase 2**: Pilot migration (4 fermentation files, 50 tests) ✅
- **Phase 3**: Full migration (8 files total, 142+ tests migrated) ✅
- **MockSessionManagerBuilder**: Eliminates session manager duplication
- **QueryResultBuilder**: Standardizes SQLAlchemy result mocking
- **EntityFactory**: Centralized mock entity creation with defaults
- **ValidationResultFactory**: Consistent validation result mocking
- **Code reduction**: ~800-1,000 lines across 8 repository test files
- **Time savings**: 50% faster test creation (45min → 15min for repositories)
- **Pattern consistency**: 100% adoption in migrated tests

### ADR-027: Structured Logging & Observability Infrastructure
**Decision:** Implement structlog for production-ready logging and observability  
**Status:** ✅ **Complete** (Dec 22, 2025)  
**Impact:** Critical - Production readiness, debugging, security audit trail  
**Key Points:**
- **Phase 1**: Core infrastructure implemented ✅
  - structlog ^25.5.0 + colorama ^0.4.6 installed
  - `configure_logging()`: JSON (prod) or Console (dev)
  - `get_logger()`: Returns BoundLogger with automatic context
  - `LogTimer`: Context manager for performance measurement
  - `sanitize_log_data()`: Redact passwords, tokens, PII
  - `LoggingMiddleware`: Correlation IDs, request/response timing
  - `UserContextMiddleware`: Bind user_id, winery_id from auth
- **Phase 2**: Repository layer logging ✅
  - 6 repositories: Fermentation, Sample, Winery, Vineyard, HarvestLot
  - CRUD operations logged (create, get, update, delete)
  - Query operations with filters logged
  - Sensitive data sanitization applied
  - 84/84 repository tests passing
- **Phase 3**: Service layer logging ✅
  - 3 services: FermentationService, SampleService, ValidationOrchestrator
  - Business operations logged (create fermentation, add sample, status updates)
  - Validation failures logged with error details
  - LogTimer measuring critical operations
  - 66/66 service tests passing
- **Phase 4**: API layer integration ✅
  - **main.py created**: Production FastAPI app with middleware
  - **LoggingMiddleware**: Correlation IDs, request/response timing
  - **UserContextMiddleware**: Automatic user context binding
  - **error_handlers.py enhanced**: All exceptions logged before HTTP response
  - Logging includes: correlation_id, error_type, endpoint, status_code
  - Manual testing verified (4/4 tests passed)
  - Production ready: `uvicorn src.main:app --host 0.0.0.0 --port 8000`
- **Phase 5**: Testing & documentation ✅
  - **Logging Best Practices Guide**: Complete guide for developers
  - **Production Deployment Checklist**: Pre/post deployment validation
  - CloudWatch/ELK/Datadog integration examples
  - Troubleshooting guide with common scenarios
  - Security checklist (sanitization, audit trail)
  - Performance baselines documented
- **Final Status**: All 5 phases complete, production ready ✅
- **Timeline**: 6 days total (Dec 16-22, 2025)
- **Context propagation**: correlation_id, winery_id, user_id automatic
- **Security**: Full audit trail (WHO did WHAT WHEN)
- **Performance**: LogTimer measuring DB operations, business logic
- **Production**: CloudWatch/ELK/Datadog compatible (JSON output)
- **Tests**: 150/150 passing (84 repository + 66 service)
- **API Ready**: main.py created, middleware integrated, error handlers enhanced
- **Manual Test**: 4/4 tests passed (correlation IDs, user context, error logging, timing)

### ADR-014: Fruit Origin Service Layer Architecture
**Decision:** Unified FruitOriginService for vineyard and harvest lot operations  
**Status:** ✅ **Implemented** (Dec 27, 2025)  
**Impact:** Complete Fruit Origin module service layer  
**Key Points:**
- **Architecture**: Unified service (like FermentationService)
- **Operations**: 8 methods (vineyard CRUD + harvest lot CRUD)
- **Business Rules**: Harvest date validation, cascade delete validation
- **Security**: ADR-025 integrated (winery_id enforcement)
- **Error Handling**: ADR-026 domain errors (5 new error types)
- **Logging**: ADR-027 structured logging with LogTimer
- **Testing**: 28 service tests (15 vineyard + 13 harvest lot)
- **Total Tests**: 100/100 passing (72 repo + 28 service)
- **Full Suite**: 590/590 tests passing (zero regressions)
- **Grape Model**: Single variety per harvest lot (MVP simplification)
- **Cross-winery**: Allowed (buying grapes scenario)

### ADR-015: Fruit Origin API Design & REST Endpoints
**Decision:** REST API for vineyard and harvest lot management with FastAPI  
**Status:** ✅ **COMPLETE** (All 3 Phases - Dec 29, 2025)  
**Impact:** Complete API layer for Fruit Origin module with 100% test coverage  
**Key Points:**
- **Phase 1**: Vineyard API - 16/16 tests passing (100%) ✅
  - 6 endpoints: POST, GET, GET list, PATCH, DELETE, GET with include_deleted
  - Multi-tenancy enforcement (winery_id filtering)
  - Code uniqueness validation, soft delete support
- **Phase 2**: Harvest Lot API MVP - Initial implementation ✅
  - 3 endpoints: POST, GET, GET list
  - Business rule validation (harvest date, block existence)
- **Phase 3**: Complete Harvest Lot CRUD - 18/18 tests passing (100%) ✅
  - Added: PATCH (update), DELETE (soft delete)
  - Service layer: update_harvest_lot (52 lines), delete_harvest_lot (43 lines)
  - Alternative test strategy: positive tests replace XFAIL markers
- **Test Quality**: Zero XFAIL, 100% pass rate
  - Unit tests: 100/100 passing (vineyard + harvest lot operations)
  - Integration tests: 43/43 passing
  - API tests: 34/34 passing (16 vineyard + 18 harvest lot)
  - **Total: 177/177 Fruit Origin tests passing**
- **Test Improvements**: 
  - Fixed 3 failing vineyard delete unit tests (mock get_session)
  - Replaced 2 vineyard XFAIL tests with alternatives
  - Renamed test_harvest_lot_api_mvp.py → test_harvest_lot_api.py
- **Integration**: Added to run_all_tests.ps1 (709 total tests passing)
- **Architecture**: Follows ADR-006 patterns (FastAPI, Pydantic v2, JWT auth)
- **Security**: ADR-025 multi-tenancy enforcement throughout
- **Error Handling**: ADR-026 domain errors with proper HTTP status codes
- **Phase 4**: Future Integration - Deferred (requires fermentation module)

### ADR-016: Winery Service Layer Architecture
**Decision:** Service layer with WineryService implementing business logic and validation  
**Status:** ✅ **COMPLETE** (All 5 Phases - Dec 29, 2025)  
**Impact:** Complete service layer for Winery module with integration tests  
**Key Points:**
- **Phase 1-4**: Foundation complete (entity, repository, DTOs)
  - Winery entity with `code` field (business identifier)
  - WineryRepository with get_by_code(), list_all(), count()
  - 44 repository tests (22 unit + 22 integration)
- **Phase 5**: Service Layer + Integration Tests ✅
  - IWineryService interface (9 abstract methods)
  - WineryService implementation (392 lines)
  - 9 methods: create, get, get_by_code, list, update, delete, exists, check_can_delete, count
  - 22 unit tests (100% passing)
  - 17 integration tests (100% passing)
- **Architecture Patterns**:
  - ValidationOrchestrator pattern (consistent with ADR-014)
  - Delete protection: validation + DB constraints (dual layer)
  - Cross-module validation (vineyard + fermentation dependencies)
  - No caching initially (YAGNI principle)
- **Error Handling**:
  - WineryHasActiveDataError for delete protection
  - WineryNotFoundError, DuplicateWineryError
  - ADR-026 domain error patterns
- **Security & Logging**:
  - ADR-025 multi-tenancy enforcement (winery_id)
  - ADR-027 structured logging with LogTimer
- **Test Results**:
  - Unit: 44/44 (22 repository + 22 service)
  - Integration: 35/35 (18 repository + 17 service)
  - **Total: 79/79 Winery tests (100%)**
  - **System: 748/748 tests (100%)**
- **Cross-Module Impact**: Fixed 39 Fruit Origin tests (code field added to fixtures)
- **Timeline**: December 29, 2025 (1 day implementation)

### ADR-029: Data Source Field for Historical Data Tracking
**Decision:** Add data_source field to Fermentation/Sample entities instead of creating separate HistoricalFermentation entities  
**Status:** ✅ **IMPLEMENTED** (Jan 2, 2026)  
**Impact:** Medium - Enables historical data tracking without entity duplication  
**Key Points:**
- **Implementation**: 32 new tests passing (6 enum + 16 entity + 8 repository + 2 interface)
- **Field**: `data_source: Mapped[str]` with enum values (SYSTEM, IMPORTED, MIGRATED)
- **Additional**: `imported_at: Mapped[datetime]` (nullable) for import timestamp
- **Benefits**: Auditing, debugging, UI differentiation, future-proofing
- **Cost**: Only 20 bytes per record
- **Index**: Created on data_source for query performance
- **Database**: PostgreSQL tables recreated with new columns
- **Repository Methods**: 
  - `FermentationRepository.list_by_data_source()`
  - `SampleRepository.list_by_data_source()`
- **Logging**: Structured logging with ADR-027 (LogTimer, context binding)
- **Total Tests**: 914/914 system-wide tests passing
- **Alternative rejected**: Separate HistoricalFermentation tables (massive code duplication)
- **Alternative rejected**: Boolean is_historical (not extensible)
- **Alternative rejected**: YAGNI/no field (loses auditing capability)
- **Ready For**: ADR-018 (Historical Data Module), ADR-019 (ETL Pipeline)

### ADR-019: ETL Pipeline Design for Historical Data
**Decision:** pandas-based ETL pipeline with 3-layer validation and upsert strategy  
**Status:** ✅ **Approved** (Dec 30, 2025)  
**Impact:** High - Enables historical data import from Excel  
**Key Points:**
- **Library**: pandas + openpyxl (read and write Excel)
- **Validation**: 3 layers (pre-validate schema, row-validate data, post-validate integrity)
- **Error handling**: Best-effort with detailed report (ImportResult)
- **Excel error report**: Auto-generated Excel with errors/warnings highlighted
  - Error rows in red, warning rows in yellow
  - Additional columns: 'Errors' and 'Warnings'
  - Download endpoint: GET /import/{job_id}/error-report
- **Async**: FastAPI Background Tasks (MVP), migrate to Celery if needed
- **Excel format**: 1 row = 1 sample, fermentation metadata repeats
- **Re-import**: Upsert strategy (UPDATE by winery_id + code + data_source)
- **Sample merge**: Match by measured_at (update if exists, create if not)
- **Performance targets**: 1K rows < 30s, 10K rows < 5min, memory < 500MB
- **Success rate**: 95%+ valid rows imported successfully
- **No data loss**: Valid rows always imported even if others fail

### ADR-030: ETL Cross-Module Architecture & Performance Optimization
**Decision:** Refactor ETL to use service layer for cross-module orchestration and eliminate N+1 queries  
**Status:** ✅ **Accepted** (Jan 6, 2026)  
**Impact:** High - Fixes critical architectural and performance issues in ETL pipeline  
**Key Points:**
- **Problem Analysis**: N+1 queries (1000 fermentations = 1000 SELECT), cross-module coupling, all-or-nothing transactions
- **Service Layer**: Create `FruitOriginOrchestrationService` to encapsulate vineyard/block/harvest lot creation
- **Performance**: Batch vineyard loading (99.9% query reduction: 1000 queries → 1 query)
- **Resource Optimization**: Single shared "IMPORTED-DEFAULT" VineyardBlock per vineyard (not per fermentation)
- **Partial Success**: Independent transactions per fermentation (999/1000 valid → 999 saved)
- **Progress Tracking**: Async callback mechanism for real-time updates + cancellation support
- **Optional Fields**: vineyard_name and grape_variety optional with defaults ("UNKNOWN", "Unknown")
- **Security**: winery_id and user_id from auth context (JWT), not Excel columns
- **Tests**: 43/43 unit tests passing (includes 5 new tests for edge cases)
- **Development Environment**: Poetry-managed dependencies (pandas 2.3.3, openpyxl 3.1.5)
- **Architecture**: Loose coupling via IFruitOriginOrchestrationService interface
- **Phase 1 Complete**: Optional fields, context parameters, validation updates
- **Phase 2 Pending**: Service creation, batch optimization, progress tracking
- **Evaluation Score**: 6.5/10 (functional but needs performance/architecture fixes)
- **Documentation**: Detailed analysis in `docs/etl-architecture-refactoring.md`
- **Idempotent**: Re-importing doesn't duplicate data
- **User-friendly**: Download Excel to see exactly what needs fixing

### ADR-028: Module Dependency Management Standardization
**Decision:** Standardize all modules with independent Poetry-managed environments  
**Status:** ✅ **FULLY IMPLEMENTED** (All 4 Phases - Dec 23, 2025)  
**Impact:** Module independence, better CI/CD, microservices-ready  
**Key Points:**
- **Problem**: Inconsistent dependency management across modules
- **Solution**: Each module gets independent Poetry environment with explicit dependencies
- **Implementation**: All 4 phas7, 2025)

**Implementation Complete:**
- ✅ Domain Layer (Entities, DTOs, Enums, Interfaces)
- ✅ **Repository Layer**: ALL repositories implemented (5 new repositories)
  - FermentationRepository, SampleRepository, LotSourceRepository ✅
  - HarvestLotRepository, VineyardRepository, VineyardBlockRepository ✅
  - WineryRepository, FermentationNoteRepository ✅
  - **Total**: 194 repository tests passing (113 unit + 81 integration)
- ✅ Service Layer (FermentationService + SampleService + Validators)
- ✅ **Winery Service Layer**: WineryService implemented (ADR-016)
  - 22 unit tests + 17 integration tests = 39 service layer tests
  - 79/79 total Winery tests (44 repository + 35 integration)
- ✅ **Fruit Origin Service Layer**: FruitOriginService implemented (ADR-014)
  - 28 service tests (15 vineyard + 13 harvest lot)
  - 100/100 total tests (72 repo + 28 service)
- ✅ Auth Module (shared/auth with JWT, RBAC, multi-tenancy)
- ✅ **API Layer (All Phases)**: Complete endpoint suite with real database
- ✅ **Error Handling Refactoring**: Centralized with decorator pattern
- ✅ Total: **748/748 tests passing (100%)**
  - Fermentation: 234 tests
  - Fruit Origin: 177 tests (100 repo/service + 77 api/integration)
  - Winery: 79 tests (44 unit + 35 integration)14 COMPLETE**: Fruit Origin Service Layer (Dec 27, 2025)
  - FruitOriginService implemented with 8 methods
  - 28 service tests passing (15 vineyard + 13 harvest lot)
  - Business rules: harvest date validation, cascade delete
  - Security (ADR-025), error handling (ADR-026), logging (ADR-027) integrated
  - 100/100 tests passing (72 repo + 28 service)
  - Full test suite: 590/590 passing (zero regressions)
- ✅ **ADR-027 COMPLETE**: Structured Logging & Observability (Dec 22, 2025)
  - All 5 phases complete: Infrastructure, Repository, Service, API, Documentation
  - 150/150 tests passing (84 repository + 66 service)
  - Production ready with logging best practices and deployment checklist
- ✅ **ADR-028 COMPLETE**: Module Dependency Management Standardization (Dec 23, 2025)
  - All 4 phases complete: Winery, Fruit Origin, Documentation, Shared
  - 692+ unit tests passing across all modules
- ✅ **Repository Layer**: ALL repositories implemented (5 new repositories)
  - FermentationRepository, SampleRepository, LotSourceRepository ✅
  - HarvestLotRepository, VineyardRepository, VineyardBlockRepository ✅
  - WineryRepository, FermentationNoteRepository ✅
  - **Total**: 194 repository tests passing (113 unit + 81 integration)
- ✅ Service Layer (FermentationService + SampleService + Validators)
- ✅ **Fruit Origin Service Layer**: FruitOriginService implemented (ADR-014)
  - 28 service tests (15 vineyard + 13 harvest lot)
  - 100/100 total tests (72 repo + 28 service)
- ✅ **Winery Service Layer**: WineryService implemented (ADR-016)
  - 22 unit tests + 17 integration tests = 39 service layer tests
  - 79/79 total Winery tests (44 repository + 35 integration)
- ✅ Auth Module (shared/auth with JWT, RBAC, multi-tenancy)
- ✅ **API Layer (All Phases)**: Complete endpoint suite with real database
- ✅ **Error Handling Refactoring**: Centralized with decorator pattern
- ✅ Total: **748/748 tests passing (100%)**
  - Fermentation: 234 tests
  - Fruit Origin: 177 tests (100 repo/service + 77 integration/api)
  - Winery: 79 tests (44 unit + 35 integration)
  - Auth: 159 tests
  - Shared: 52 tests + 47 testing infrastructure

**Current Phase:**
- ✅ **ADR-027 COMPLETE**: Structured Logging & Observability (Dec 22, 2025)
  - All 5 phases complete: Infrastructure, Repository, Service, API, Documentation
  - 150/150 tests passing (84 repository + 66 service)
  - Production ready with logging best practices and deployment checklist
- ✅ **ADR14 Complete: Fruit Origin Service Layer implemented (Dec 27, 2025)
  - FruitOriginService: 8 methods (vineyard CRUD + harvest lot CRUD)
  - 28 service tests passing (15 vineyard + 13 harvest lot)
  - Business rules: harvest date validation, cascade delete validation
  - 5 new domain errors (VineyardHasActiveLotsError, etc.)
  - Full integration: ADR-025 (security), ADR-026 (errors), ADR-027 (logging)
  - 100/100 tests passing (72 repo + 28 service)
  - Zero regressions (590/590 full test suite)
- ✅ ADR-0-028 COMPLETE**: Module Dependency Management Standardization (Dec 22, 2025)
  - All 3 phases complete: Winery, Fruit Origin, Documentation
  - 317/317 unit tests passing across all modules (fermentation, winery, fruit_origin)
  - Comprehensive module-setup-guide.md created
  - All modules now independent with Poetry-managed environments

**Recent Achievements (December 2025):**
- ✅ ADR-016 Complete: Winery Service Layer implemented (Dec 29, 2025)
  - WineryService: 9 methods (create, get, get_by_code, list, update, delete, exists, check_can_delete, count)
  - 22 unit tests + 17 integration tests = 39 service layer tests
  - Total: 79/79 Winery tests (44 repository + 35 integration)
  - Cross-module fixes: 39 Fruit Origin tests updated for code field
  - System: 748/748 tests passing (100%)
- ✅ ADR-015 Complete: Fruit Origin API Layer implemented (Dec 29, 2025)
  - Phase 1-3: Complete vineyard + harvest lot CRUD (34 API tests)
  - 177/177 Fruit Origin tests passing (100 unit + 43 integration + 34 API)
- ✅ ADR-014 Complete: Fruit Origin Service Layer implemented (Dec 27, 2025)
  - FruitOriginService: 8 methods (vineyard CRUD + harvest lot CRUD)
  - 28 service tests + 72 repository tests = 100/100 passing
- ✅ ADR-009 Complete: 5 new repositories implemented with full test coverage
  - WineryRepository: 22 unit + 18 integration tests
  - VineyardRepository: 28 unit + 11 integration tests
  - VineyardBlockRepository: 31 unit + 12 integration tests
  - HarvestLotRepository: 13 unit + 20 integration tests
  - FermentationNoteRepository: 19 unit + 20 integration tests
- ✅ ADR-011 Complete: Integration test infrastructure refactored (Dec 13, 2025)
  - **635 lines eliminated** (79% reduction in test code duplication)
  - **Shared testing utilities created** (641 lines, 52/52 tests passing)
  - **3 modules migrated** to shared infrastructure (winery, fruit_origin, fermentation)
  - **Metadata blocker fixed**: All tests run together without errors (61/61 passing)
- ✅ ADR-012 Complete: Unit test infrastructure refactored (Dec 15, 2025)
  - **800-1,000 lines eliminated** across 8 repository test files
  - **4 core utilities**: MockSessionManagerBuilder, QueryResultBuilder, EntityFactory, ValidationResultFactory
  - **50% time savings**: Test creation time reduced from 45min → 15min

**Code Metrics:**
- Repositories: 9/9 implemented (100%) ✅
- Repository tests: 194/194 passing (100%) ✅
- Service layer: 3/3 modules complete (Fermentation, Fruit Origin, Winery) ✅
- Integration test infrastructure: 52/52 utility tests passing ✅
- Total test suite: 748/748 tests passing (100%) ✅
- Test coverage: Comprehensive (unit + integration + API for all modules)
- Code reduction: 635 lines eliminated from integration tests + 800-1,000 from unit tests ✅

**Next Steps:**
1. ✅ ~~Implement ADR-011 (Integration test infrastructure)~~ **COMPLETE**
2. ✅ ~~Implement ADR-012 (Unit test infrastructure)~~ **COMPLETE Phase 3**
3. ✅ ~~Implement ADR-014 (Fruit Origin Service Layer)~~ **COMPLETE**
4. ✅ ~~Implement ADR-015 (Fruit Origin API Layer)~~ **COMPLETE**
5. ✅ ~~Implement ADR-016 (Winery Service Layer)~~ **COMPLETE**
6. Implement ADR-017 (Winery API Layer)
7. Continue with ADR-018+ for Historical Data, Analysis Engine, etc.

---

## 🔗 Related Documentation

- **System Context:** [project-context.md](../project-context.md)
- **Architecture:** [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md)
- **Structure:** [PROJECT_STRUCTURE_MAP.md](../PROJECT_STRUCTURE_MAP.md)
- **Collaboration:** [collaboration-principles.md](../collaboration-principles.md)

---

## 📝 ADR Template Guide

When creating new ADRs, use:
- **[ADR-template-light.md](./ADR-template-light.md)** - For simple decisions (4 sections)
- **[ADR-template.md](./ADR-template.md)** - For complex decisions (11 sections)
- **[ADR-template-selection-guide.md](./ADR-template-selection-guide.md)** - Decision matrix

**Template Rules:**
- Keep ADRs concise (< 200 lines)
- Focus on decisions, not implementation details
- Use Quick Reference for developers
- Update this index when adding new ADRs

# Component Context: Service Component (Fermentation Management Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Business logic orchestration and validation** for fermentation and sample management operations within the Fermentation Management Module.

**Position in module**: Application layer coordinating between domain models and repository persistence, enforcing business rules and validation before data operations.

**Architectural Decision:** Following ADR-005, this component implements strict separation between domain services (FermentationService, SampleService) and validation services (5 specialized validators) with dependency injection for repository abstractions.


## Architecture pattern
**Service Layer Pattern** with dependency injection and validation orchestration.

**Design approach**: Orchestrate business operations using domain entities and repository abstractions, with specialized validation services for different concerns (value validation, chronology, business rules).

- **Service Interfaces**: IFermentationService (7 methods), ISampleService (6 methods), 5 validation service interfaces
- **Concrete Services**: FermentationService, SampleService (implement domain business logic)
- **Validation Layer**: ValidationOrchestrator, ValueValidationService, ChronologyValidationService, BusinessRuleValidationService, ValidationService
- **Error Hierarchy**: ServiceError → ValidationError, NotFoundError, DuplicateError, BusinessRuleViolation
- **Data flow**: API Layer → Service Interface → Service Implementation → Repository → Database
- **Extension points**: Additional validation services, business rule engines, event handlers
- **Integration strategy**: Dependency injection provides repository implementations from Repository Component

## Component interfaces

### **Receives from (API Layer - Future)**
- Command DTOs: Create/update requests with validated input data
- Query parameters: Filtering, pagination, sorting for list operations
- User context: winery_id, user_id for multi-tenancy and authorization

### **Provides to (API Layer - Future)**
- Domain entities: Fermentation and Sample objects with complete data
- Operation results: Success/failure status with validation errors
- Business rule violations: Detailed error information for user feedback

### **Uses (Repository Component)**
- IFermentationRepository: Fermentation persistence operations (5 methods)
- ISampleRepository: Sample persistence operations (11 methods)
- Transaction coordination: Multi-repository operations for consistency

## Key patterns implemented
- **Service Layer Pattern**: Business logic orchestration separate from persistence
- **Dependency Injection**: Repository abstractions injected via constructors
- **Validation Chain**: Orchestrated validation with multiple specialized validators
- **Result Pattern**: ValidationResult objects with success/failure/warnings
- **Command-Query Separation**: Clear separation between read and write operations

## Business rules enforced
- **Multi-tenancy isolation**: All operations scoped to winery_id
- **Fermentation lifecycle**: Status transitions with validation (draft→active→completed)
- **Sample validation**: Value ranges, chronological ordering, business rules
- **Soft deletes**: Logical deletion maintaining audit trail
- **Completion rules**: Duration minimums, residual sugar checks for fermentation completion

## Connection with other components
**Repository Component**: Receives IFermentationRepository, ISampleRepository via dependency injection  
**Domain Component**: Uses domain entities (Fermentation, BaseSample) and enums (FermentationStatus)

## Implementation status

**Status:** ✅ **Service Layer Complete** (Ready for API integration)  
**Reference:** ADR-005-service-layer-interfaces.md

**Note:** All business logic and validation implemented. Waiting for API layer to expose via HTTP endpoints.

### Implemented Components

**FermentationService** ✅ COMPLETE
- **Methods:** 7 (create, get_by_id, get_by_winery, update_status, complete, soft_delete, validate)
- **Tests:** 33 passing (lifecycle, validation, error handling)
- **Status:** Fully implemented with repository integration
- **Compliance:** ADR-005 compliant (zero direct repository access)

**SampleService** ✅ COMPLETE
- **Methods:** 6 (add_sample, get_sample, get_by_fermentation, get_latest_sample, get_in_timerange, validate_sample_data)
- **Tests:** 27 passing (CRUD operations, queries, validation)
- **Status:** Fully implemented with validation orchestration
- **Compliance:** ADR-005 compliant (uses validation services)

**Validation Services** ✅ COMPLETE (55 tests total)
- **ValidationOrchestrator:** 4 tests (complete validation workflow)
- **ValueValidationService:** 9 tests (range validation, type checking)
- **ChronologyValidationService:** 14 tests (timeline validation, ordering)
- **BusinessRuleValidationService:** 9 tests (sugar trends, temperature ranges)
- **ValidationService:** 19 tests (result patterns, error aggregation)

**📋 Proposed Services (ADR-032 - Jan 13, 2026):**
- **HistoricalDataService**: Query and aggregate historical fermentation data
  - 4 methods: get_historical_fermentations, get_historical_fermentation_by_id, get_fermentation_samples, extract_patterns
  - Multi-tenant security: Auto-scoped by winery_id
  - Reuses: FermentationRepository, SampleRepository with `data_source='HISTORICAL'` filter
  - Test plan: 12 unit tests, estimated 2 hours
  - Part of Historical Data API Layer (ADR-032)

**ETLService** ✅ COMPLETE (33 tests total)
- **Methods:** 3 main (import_fermentations, _import_single_fermentation, _validate_csv_data) + 3 orchestration helpers
- **Tests:** 21 unit + 12 integration = 33 tests
- **Architecture:** Cross-module orchestration with TransactionScope pattern
- **Features:**
  - 3-layer validation (CSV format → business rules → chronology)
  - Partial success support (some fermentations succeed, others fail)
  - Progress tracking with callbacks
  - Cancellation token for user-initiated abort
  - Per-fermentation transactions with automatic rollback
  - Batch vineyard loading (N+1 query elimination)
- **Performance:** 100 fermentations in ~4.75s (< 10% overhead)
- **Dependencies:** FruitOriginService (ADR-030), TransactionScope (ADR-031)
- **References:** ADR-019 (ETL design), ADR-030 (cross-module architecture), ADR-031 (transaction coordination)

### Test Coverage
- **Total:** 148 tests passing (115 original + 33 ETL)
- **FermentationService:** 33 tests (lifecycle operations)
- **SampleService:** 27 tests (sample management)
- **Validation Services:** 55 tests (all validation logic)
- **ETLService:** 33 tests (21 unit + 12 integration)
- **Integration:** Unit tests use mocked repositories, ETL integration tests use real database

### Completed Features
1. ✅ **FastAPI endpoints** for fermentation and sample management (90 API tests)
2. ✅ **DTO models** for API request/response serialization
3. ✅ **Authentication/Authorization** integration with winery context
4. ✅ **API documentation** with OpenAPI/Swagger specifications
5. ✅ **ETL Pipeline** for historical data import with validation (ADR-019, ADR-030, ADR-031)

## Key implementation considerations
- **Async operations**: All service methods async for FastAPI compatibility
- **Error handling**: Specific exception types for different failure scenarios
- **Validation orchestration**: Composable validation services for extensibility
- **Multi-tenancy**: All operations filtered by winery_id for data isolation
- **Type safety**: Strict typing with domain entities and DTOs

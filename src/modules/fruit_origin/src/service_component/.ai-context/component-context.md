# Component Context: Service Component (Fruit Origin Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Business logic orchestration and validation** for vineyard hierarchy management and harvest recording workflows within the Fruit Origin Module.

**Position in module**: Application layer coordinating between domain models and repository persistence, enforcing business rules and validation before data operations.

**Architectural Decision:** Following ADR-014, this component implements strict separation between domain services (VineyardService, VineyardBlockService, HarvestLotService) and validation services (ValidationOrchestrator with 3 specialized validators) using dependency injection for repository abstractions.

## Architecture pattern
**Service Layer Pattern** with dependency injection and validation orchestration.

**Design approach**: Orchestrate business operations using domain entities and repository abstractions, with specialized validation services for different concerns (value validation, chronology, business rules).

- **Service Interfaces**: Not defined here - future extension point for service contracts
- **Concrete Services**: VineyardService, VineyardBlockService, HarvestLotService (implement domain business logic)
- **Validation Layer**: ValidationOrchestrator, ValueValidationService, ChronologyValidationService, BusinessRuleValidationService
- **Error Hierarchy**: ServiceError → ValidationError, EntityNotFoundError, DuplicateCodeError
- **Data flow**: API Layer → Service → Repository → Database
- **Extension points**: Additional validation services, business rule engines, event handlers
- **Integration strategy**: Dependency injection provides repository implementations from Repository Component

## Component interfaces

### **Receives from (API Layer)**
- Command DTOs: Create/update requests with Pydantic-validated input data
- Query parameters: Filtering by winery/vineyard/block, pagination, sorting
- User context: winery_id for multi-tenancy enforcement

### **Provides to (API Layer)**
- Domain entities: Vineyard, VineyardBlock, HarvestLot objects with complete data
- Operation results: Success/failure status with validation errors
- Business rule violations: Detailed ValidationResult with error list

### **Uses (Repository Component)**
- IVineyardRepository: Vineyard persistence operations (7 methods)
- IVineyardBlockRepository: Block persistence operations (7 methods)
- IHarvestLotRepository: Harvest lot persistence operations (8 methods)
- Transaction coordination: Multi-repository operations for consistency

## Key patterns implemented
- **Service Layer Pattern**: Business logic orchestration separate from persistence
- **Dependency Injection**: Repository abstractions injected via constructors
- **Validation Chain**: Orchestrated validation with three specialized validators
- **Result Pattern**: ValidationResult objects with success/failure/error aggregation
- **Command-Query Separation**: Clear separation between read and write operations
- **Multi-tenant Enforcement**: All operations automatically scoped to winery_id

## Business rules enforced
- **Multi-tenancy isolation**: All operations scoped to winery_id (security boundary)
- **Hierarchy integrity**: Cannot delete vineyard with active blocks, block with active harvest lots
- **Code uniqueness**: Unique code within winery at each hierarchy level
- **Value ranges**: brix_at_harvest (18-28°), weight_kg > 0, area_ha > 0, slope_pct (0-100)
- **Chronological consistency**: harvest_date not in future, pick_end_time > pick_start_time
- **Required fields**: Mandatory fields per entity (code, name, harvest_date, etc.)
- **Soft deletes**: Logical deletion maintaining audit trail

## Connection with other components
**Repository Component**: Receives IVineyardRepository, IVineyardBlockRepository, IHarvestLotRepository via dependency injection  
**Domain Component**: Uses domain entities (Vineyard, VineyardBlock, HarvestLot) and validation interfaces
**API Component**: Provides business logic to FastAPI routers

## Implementation status

**Status:** ✅ **Service Layer Complete** (Ready for API integration)  
**Last Updated:** December 29, 2025  
**Reference:** ADR-014-fruit-origin-service-layer.md

**Note:** All business logic and validation implemented. API layer integration complete (ADR-015). Service tests are included in the module's unit test total.

### Implemented Components

**VineyardService** ✅ COMPLETE
- **Methods:** 5 (create, get_by_id, list_by_winery, update, delete)
- **Tests:** Service tests included in module's 100 unit test total (lifecycle, validation, error handling, multi-tenancy)
- **Status:** Fully implemented with repository integration
- **Validation:** Code uniqueness, required fields, hierarchy protection
- **Compliance:** ADR-014 compliant (orchestrated validation)

**VineyardBlockService** ✅ COMPLETE
- **Methods:** 5 (create, get_by_id, list_by_vineyard, update, delete)
- **Tests:** Service tests included in module's 100 unit test total (CRUD operations, FK validation, hierarchy protection)
- **Status:** Fully implemented with vineyard relationship validation
- **Validation:** Code uniqueness within vineyard, technical spec ranges, vineyard existence
- **Compliance:** ADR-014 compliant (orchestrated validation)

**HarvestLotService** ✅ COMPLETE
- **Methods:** 6 (create, get_by_id, list_by_block, list_by_winery, update, delete)
- **Tests:** Service tests included in module's 100 unit test total (complex validation scenarios, temporal logic, multi-tenancy)
- **Status:** Fully implemented with comprehensive 19-field validation
- **Validation:** 
  - Value validation: brix range, weight > 0, temporal field formats
  - Chronology validation: harvest_date ≤ today, pick_end_time > pick_start_time
  - Business rules: block existence, code uniqueness within winery
- **Compliance:** ADR-014 compliant (orchestrated validation with error aggregation)

**ValidationOrchestrator** ✅ COMPLETE
- **Responsibility:** Coordinates three validation services in sequence
- **Services:** ValueValidationService, ChronologyValidationService, BusinessRuleValidationService
- **Pattern:** Error aggregation - collects all validation errors across all services
- **Result:** Comprehensive ValidationResult with complete error list (all-or-nothing)

**FruitOriginService** ✅ COMPLETE (ETL Orchestration Methods)
- **Purpose:** Cross-module orchestration for ETL import workflow (ADR-030)
- **Methods:** 3 orchestration methods for fermentation import
  - `batch_load_vineyards()`: Batch load vineyards by codes (N+1 elimination)
  - `get_or_create_default_block()`: Get/create "Default" block per vineyard
  - `ensure_harvest_lot_for_import()`: Get/create harvest lot for imported fermentations
- **Tests:** 13 TDD tests (batch loading, default block creation, harvest lot logic)
- **Performance:** 99% reduction in default block queries (1 query for 100 fermentations)
- **Pattern:** Service-to-service orchestration maintaining module boundaries
- **Reference:** ADR-030 (Cross-Module Architecture & Performance Optimization)

## Validation architecture

### Three-layer validation strategy
1. **ValueValidationService**: Field-level validation (types, ranges, required fields)
2. **ChronologyValidationService**: Temporal relationships and datetime logic
3. **BusinessRuleValidationService**: Domain-specific constraints and hierarchy rules

### Error aggregation
- Continues validation through all layers even if errors found
- Returns comprehensive ValidationResult with all errors
- Prevents partial validation (all-or-nothing approach)
- Provides detailed error context for API responses

## Next steps
None - Service layer complete ✅

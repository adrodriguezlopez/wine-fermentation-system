# Component Context: Service Component (Winery Module)

> **Status**: ✅ COMPLETE  
> **Implementation**: 22 unit + 17 integration tests passing (100%); API layer via api_component (25 tests)  
> **Last updated**: 2026-03-28  
> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Component responsibility
**Business logic orchestration and validation** for winery management operations within the Winery Module.

**Position in module**: Application layer coordinating between domain models and repository persistence, enforcing business rules and validation before data operations.

**Architectural Decision:** Following ADR-016, this component implements WineryService with ValidationOrchestrator pattern (consistent with Fruit Origin ADR-014) for CRUD operations with validation, global code uniqueness enforcement, and cross-module deletion protection.

## Architecture pattern
**Service Layer Pattern** with dependency injection and validation.

**Design approach**: Orchestrate business operations using domain entities and repository abstractions, with ValidationOrchestrator pattern for consistency with Fruit Origin module.

- **Service Interfaces**: IWineryService (defined in domain component)
- **Concrete Services**: WineryService (implements domain business logic)
- **Validation Strategy**: ValidationOrchestrator with ValueValidationService + BusinessRuleValidationService
- **Error Hierarchy**: ServiceError → ValidationError, WineryNotFoundError, DuplicateCodeError, WineryHasActiveDataError
- **Data flow**: API Layer → Service → Repository → Database
- **Extension points**: Caching layer (future), statistics methods (future), bulk operations (future)
- **Integration strategy**: Dependency injection provides IWineryRepository implementation from Repository Component

## Component interfaces

### **Receives from (API Layer)**
- Command DTOs: WineryCreateRequest, WineryUpdateRequest with Pydantic-validated input data
- Query parameters: Lookup by ID, code, list all wineries with pagination
- User context: For audit trail and authorization (admin operations)

### **Provides to (API Layer)**
- Domain entities: Winery objects with complete data
- Operation results: Success/failure status with validation errors
- Business rule violations: Detailed error information for duplicate codes

### **Uses (Repository Component)**
- IWineryRepository: Winery persistence operations (8 methods)
  - create, get_by_id, get_by_code, list_all, update, delete, exists_by_code, count
- **Cross-module dependencies** (for deletion protection):
  - IVineyardRepository (fruit_origin): count_by_winery() to check active vineyards
  - IFermentationRepository
- **Service Layer Pattern**: Business logic orchestration separate from persistence
- **Dependency Injection**: IWineryRepository + cross-module repositories injected via constructor
- **ValidationOrchestrator Pattern**: Consistent with Fruit Origin (ADR-014)
  - ValueValidationService: Code format, required fields validation
  - BusinessRuleValidationService: Code uniqueness, deletion protection
- **Global Code Uniqueness**: Validate code uniqueness across all wineries before persistence
- **Deletion Protection**: Proactive validation + DB constraints (two layers of safety)
- **Structured Logging**: ADR-027 integration (WHO did WHAT WHEN)
- **No Caching**: YAGNI - add Redis cache only when performance metrics justify it wineries before persistence
- **Soft Delete Protection**: Prevent deletion of wineries with active data in other modules
- **Caching Strategy**: TB
- **Global code uniqueness**: Code must be unique across all wineries (validated via repository)
- **Required fields validation**: Code and name are mandatory
- **Code format validation**: Uppercase alphanumeric with hyphens (e.g., "BODEGA-001")
- **Deletion protection**: Cannot delete winery if it has active data:
  - Active vineyards (fruit_origin.Vineyard) → check via IVineyardRepository
  - Active fermentations (fermentation.Fermentation) → check via IFermentationRepository
  - Active users (auth.User, future) → check via IUserRepository (future)
- **Two-layer protection**: Proactive service validation + DB foreign key constraints as backup
- **Code immutability**: Winery code cannot be updated after creation (business rule
  - Has active fermentations (fermentation module)
  - Has active users (auth module, future)
- **Cross-module coordination**: TBD (how to check active data in other modules?)

## Connection with other components
**API Component**: Receives command DTOs and returns domain entities  
**Repository Component**: Uses IWineryRepository for data persistence  
**Domain Component**: Uses Winery entity, IWineryService interface, DTOs, domain errors

## Implementation status

✅ **COMPLETE** (ADR-016 ✅, ADR-017 ✅)  
- 22 unit tests passing (service logic, validation, error handling)  
- 17 integration tests passing (full CRUD with real database)  
- API layer complete via api_component (25 API tests, ADR-017)

### Decisions Made (ADR-016)
**1. Validation Strategy**: ✅ ValidationOrchestrator pattern (consistent with Fruit Origin)  
**2. Caching Strategy**: ✅ No caching initially (YAGNI - add later if needed)  
**3. Deletion Protection**: ✅ Proactive validation + DB constraints (two layers)  
**4. Service Interface**: ✅ Define IWineryService interface (testability + consistency)  
**5. Errors**: ✅ Create WineryHasActiveDataError (clarity for frontend)  
**6. Logging**: ✅ Standard ADR-027 patterns (WHO, WHAT, WHEN)  
**7. Methods**: ✅ 8 core methods (no statistics until needed)ility

5. **Error Handling**:
   - Reuse existing DuplicateCodeError from domain?
   - Create WinerySpecificErrors (e.g., WineryHasActiveDataError)?
   - Recommendation: Reuse existing + add new if needed

### Methods to Implement (estimated)

**WineryService** (8-10 methods):
- `create_winery(winery_data: WineryCreateDTO) -> Winery`
- `get_winery(winery_id: int) -> Winery`
- `get_winery_by_code(code: str) -> Winery`
- `list_wineries(skip: int = 0, limit: int = 100) -> List[Winery]`
- `update_winery(winery_id: int, winery_data: WineryUpdateDTO) -> Winery`
- `delete_winery(winery_id: int) -> None` (with protection checks)
- `winery_exists(winery_id: int) -> bool`
- `count_wineries() -> int`
- `validate_code_uniqueness(code: str, exclude_id: Optional[int] = None) -> bool` (helper)
- `check_can_delete(winery_id: int) -> bool` (helper for deletion protection)

**Test Coverage** (22 unit + 17 integration = 39 tests passing):
- Create winery (success, duplicate code)
- Get winery (success, not found)
- Get by code (success, not found)
- List wineries (empty, paginated)
- Update winery (success, not found, duplicate code on update)
- Delete winery (success, not found, has active data)
- Validation helpers (code uniqueness, can delete checks)

**Estimated Effort:** 1 day (simpler than Fruit Origin - only 1 entity)

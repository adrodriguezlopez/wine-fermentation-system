# Component Context: API Component (Winery Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`
> **Related ADR**: [ADR-017: Winery API Design](../../../../.ai-context/adr/ADR-017-winery-api-design.md)

## Component responsibility
**HTTP REST API interface** for winery management operations, providing authenticated and authorized access to winery administration functionality via an admin-only namespace.

**Position in module**: Presentation layer exposing HTTP endpoints with JWT authentication, role-based access control (RBAC), request/response serialization, and special authorization logic (users can access only their own winery, admins can access all).

**Architectural Decision:** Following ADR-017, this component implements FastAPI router with Pydantic v2 schemas for winery CRUD operations and relationship navigation, integrated with shared auth module (ADR-007) for JWT authentication and RBAC, using admin namespace (`/api/v1/admin/wineries`) due to winery being a top-level entity.

## Architecture pattern
**RESTful API Pattern** with FastAPI framework, dependency injection, and role-based authorization.

**Design approach**: Clean separation between router (endpoint definitions), schemas (request/response DTOs), and business logic (service layer), with auth dependencies injecting UserContext for authorization checks.

- **Router**: winery_router (8 endpoints: 6 CRUD + 2 relationships)
- **Request Schemas**: WineryCreateRequest, WineryUpdateRequest (Pydantic v2)
- **Response Schemas**: WineryResponse, PaginatedWineriesResponse, VineyardSummaryResponse, FermentationSummaryResponse (Pydantic v2)
- **Authentication**: JWT token validation via `get_current_user` dependency from shared auth module
- **Authorization**: 
  - CREATE/DELETE/LIST: ADMIN only via `require_admin` dependency
  - GET/UPDATE: Users can access own winery, ADMIN can access all
  - Custom authorization logic: `check_winery_access(winery_id, user)`
- **Admin Namespace**: All endpoints under `/api/v1/admin/wineries` (root entity, privileged operations)
- **Error Handling**: HTTP exception handlers mapping service errors to appropriate status codes (409 conflict, 400 validation, 403 forbidden)
- **Data flow**: HTTP Request → Auth Middleware → Authorization Check → Router → Service Layer → Response Serialization
- **Extension points**: Statistics endpoints, bulk operations, audit trail
- **Integration strategy**: Depends on service_component for business logic, shared/auth for authentication, and cross-module repositories for relationships

## Component interfaces

### **Receives from (HTTP Clients)**
**Core CRUD endpoints (6):**
- **POST /api/v1/admin/wineries**: Create winery (ADMIN only) with JWT token
- **GET /api/v1/admin/wineries/{id}**: Retrieve winery by ID (users: own, ADMIN: all)
- **GET /api/v1/admin/wineries/code/{code}**: Retrieve winery by code (users: own, ADMIN: all)
- **GET /api/v1/admin/wineries**: List all wineries with pagination (ADMIN only)
- **PATCH /api/v1/admin/wineries/{id}**: Update winery data (users: own, ADMIN: all)
- **DELETE /api/v1/admin/wineries/{id}**: Soft delete winery (ADMIN only)

**Relationship endpoints (2):**
- **GET /api/v1/admin/wineries/{id}/vineyards**: List vineyards for winery (users: own, ADMIN: all)
- **GET /api/v1/admin/wineries/{id}/fermentations**: List fermentations for winery (users: own, ADMIN: all)

### **Provides to (HTTP Clients)**
- JSON responses with Pydantic serialization
- HTTP status codes: 200 (OK), 201 (Created), 204 (No Content), 400 (Validation Error), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 500 (Server Error)
- OpenAPI documentation: Swagger UI at /docs, ReDoc at /redoc
- Detailed validation error messages for client-side feedback
- Authorization-aware responses (403 for cross-winery access attempts)

### **Uses (Internal Dependencies)**
- **Service Component**: WineryService for business logic (9 methods: create, get, get_by_code, list, update, delete, exists, check_can_delete, count)
- **Auth Module** (shared/auth): `get_current_user`, `require_admin` dependencies for authentication and authorization
- **Cross-Module Repositories** (for relationships):
  - VineyardRepository (fruit_origin module) for vineyard listing
  - FermentationRepository (fermentation module) for fermentation listing
- **Domain Entities**: Winery entity for type hints and response serialization
- **Domain Errors**: WineryNotFoundError, DuplicateWineryError, WineryHasActiveDataError

## Key patterns implemented
- **Admin Namespace**: `/api/v1/admin/*` prefix for privileged operations (winery is root entity)
- **RESTful API Design**: Resource-based URLs with standard HTTP methods
- **Dependency Injection**: FastAPI dependencies for auth, services, database sessions
- **Role-Based Authorization**: ADMIN-only operations (create, delete, list) + user self-service (get/update own winery)
- **Custom Authorization**: `check_winery_access()` helper for flexible access control
- **Request/Response DTOs**: Pydantic schemas for validation and serialization
- **Error Handling**: Consistent JSON error responses with HTTP status codes
- **API Versioning**: `/api/v1` prefix for future backward compatibility
- **OpenAPI**: Auto-generated documentation from Pydantic schemas
- **Pagination**: Standard limit/offset pattern with total count metadata
- **Soft Deletes**: Deleted entities excluded from queries

## Business rules enforced
- **Admin-only operations**: CREATE, DELETE, LIST restricted to ADMIN role
- **Self-service authorization**: Users can GET/UPDATE only their own winery (checked via JWT winery_id)
- **Cross-winery blocking**: HTTP 403 if user attempts to access different winery
- **Input validation**: Pydantic field validators for data types, formats, length constraints
- **Code uniqueness**: HTTP 409 Conflict for duplicate codes (global uniqueness)
- **Name uniqueness**: HTTP 409 Conflict for duplicate names (global uniqueness)
- **Code immutability**: Code cannot be changed after creation (not allowed in update DTO)
- **Delete protection**: HTTP 400 if winery has active vineyards or fermentations (referential integrity)
- **Soft deletes**: Winery marked as deleted (is_deleted=True), excluded from queries

## Connection with other components
**Service Component**: Receives WineryService via dependency injection  
**Domain Component**: Uses Winery entity and DTOs for type hints  
**Auth Module**: Uses `get_current_user` for JWT validation and `require_admin` for RBAC  
**Fruit Origin Module**: Uses VineyardRepository for relationship endpoint  
**Fermentation Module**: Uses FermentationRepository for relationship endpoint

## Implementation status

**Status:** ✅ **IMPLEMENTED** (100% Complete)  
**Created:** January 13, 2026  
**Completed:** January 13, 2026  
**Reference:** ADR-017-winery-api-design.md

**Implementation Summary:**
- **6 Core CRUD Endpoints**: All implemented and tested (CREATE, GET by ID, GET by code, LIST, UPDATE, DELETE)
- **25 API Tests**: 100% passing (6 CREATE + 8 GET + 3 LIST + 5 UPDATE + 3 DELETE)
- **Authorization**: Role-based (ADMIN + winery-scoped access) fully enforced
- **Request/Response DTOs**: Pydantic v2 with validation
- **Error Handling**: Domain errors mapped to HTTP status codes (404, 403, 409, 400)
- **Structured Logging**: ADR-027 integration complete
- **OpenAPI Documentation**: Auto-generated Swagger/ReDoc
- **Total Module Tests**: 104 passing (44 unit + 35 integration + 25 API)
- **FastAPI App**: main.py created for standalone deployment

**Deferred to Future:**
- Relationship endpoints (GET vineyards, GET fermentations) - optional enhancement
- Seed script for bootstrap data - tracked in ADR-INDEX.md

**Prerequisites Complete:**
- ✅ WineryService implemented (ADR-016)
- ✅ Auth module with JWT + RBAC (ADR-007)
- ✅ Fruit Origin API as pattern reference (ADR-015)

### Endpoints to Implement

**Phase 1: Core CRUD** (Priority: HIGH)
- **POST /admin/wineries**: Create winery (201 Created)
  - Auth: ADMIN only
  - Tests: success, duplicate code (409), duplicate name (409), validation errors (400)
- **GET /admin/wineries/{id}**: Retrieve winery (200 OK)
  - Auth: Users (own only), ADMIN (all)
  - Tests: success, not found (404), forbidden (403), admin access
- **GET /admin/wineries/code/{code}**: Retrieve winery by code (200 OK)
  - Auth: Users (own only), ADMIN (all)
  - Tests: success, not found (404), forbidden (403)
- **GET /admin/wineries**: List wineries with pagination (200 OK)
  - Auth: ADMIN only
  - Tests: pagination, deleted exclusion, forbidden (403)
- **PATCH /admin/wineries/{id}**: Update winery (200 OK)
  - Auth: Users (own only), ADMIN (all)
  - Tests: success, not found (404), forbidden (403), validation, immutable code
- **DELETE /admin/wineries/{id}**: Soft delete winery (204 No Content)
  - Auth: ADMIN only
  - Tests: success, protection checks (400), not found (404), forbidden (403)

**Phase 2: Relationship Endpoints** (Priority: MEDIUM)
- **GET /admin/wineries/{id}/vineyards**: List vineyards (200 OK)
  - Auth: Users (own only), ADMIN (all)
  - Tests: success, empty list, forbidden (403)
- **GET /admin/wineries/{id}/fermentations**: List fermentations (200 OK)
  - Auth: Users (own only), ADMIN (all)
  - Tests: success, filtering, forbidden (403)

**Phase 3: Seed Data & Documentation**
- Create seed script for initial winery + admin user
- Document bootstrap process
- Update API documentation

## Test strategy
- **Zero XFAIL markers**: Target 100% pass rate from day 1
- **Integration testing**: Using TestClient with real database (async PostgreSQL)
- **Authorization validation**: All endpoints enforce correct role-based access
- **Cross-winery blocking**: Verify 403 responses for unauthorized access attempts
- **Error scenarios**: Comprehensive coverage of 400, 403, 404, 409 error cases
- **Admin vs User**: Separate test cases for admin and regular user access patterns

**Test Counts:**
- Phase 1: 15 CRUD tests (5 endpoints × ~3 tests each)
- Phase 2: 6 relationship tests (2 endpoints × 3 tests each)
- **Total: 21 API tests** (target 100% pass rate)

## DTOs to implement

### Request DTOs (Pydantic v2)
```python
class WineryCreateRequest(BaseModel):
    code: str  # Alphanumeric + hyphens/underscores, uppercase
    name: str  # 1-200 chars
    location: Optional[str] = None  # 0-100 chars
    notes: Optional[str] = None

class WineryUpdateRequest(BaseModel):
    name: Optional[str] = None  # Code is immutable
    location: Optional[str] = None
    notes: Optional[str] = None
```

### Response DTOs (Pydantic v2)
```python
class WineryResponse(BaseModel):
    id: int
    code: str
    name: str
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

class PaginatedWineriesResponse(BaseModel):
    items: List[WineryResponse]
    total: int
    limit: int
    offset: int

class VineyardSummaryResponse(BaseModel):
    id: int
    code: str
    name: str

class FermentationSummaryResponse(BaseModel):
    id: int
    vessel_code: str
    vintage_year: int
    status: str
```

## Error handling
- **HTTP 400 (Bad Request)**: Validation errors, business rule violations, delete protection
- **HTTP 401 (Unauthorized)**: Missing or invalid JWT token
- **HTTP 403 (Forbidden)**: Insufficient role (not ADMIN) or cross-winery access attempt
- **HTTP 404 (Not Found)**: Winery not found
- **HTTP 409 (Conflict)**: Duplicate code or name (global uniqueness)
- **HTTP 500 (Internal Server Error)**: Unexpected errors with error ID for tracking

## Authorization logic
```python
async def check_winery_access(
    winery_id: int,
    user: UserContext,
    require_admin: bool = False
) -> None:
    """
    Verify user can access winery.
    
    Rules:
    - ADMIN: Can access any winery
    - Regular users: Can only access their own winery (winery_id from JWT)
    - If require_admin=True: Only ADMIN allowed
    
    Raises:
        HTTPException 403: Access denied
    """
    if require_admin and user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if user.role != "ADMIN" and user.winery_id != winery_id:
        raise HTTPException(status_code=403, detail="Access denied to this winery")
```

## Bootstrap strategy
**Challenge:** First winery cannot be created without authenticated user.

**Solution: Database Seed Script**
```bash
# Run once during initial setup
poetry run python scripts/seed_initial_data.py
```

Creates:
1. Initial winery (code: "ADMIN-WINERY")
2. Admin user (email: "admin@winery-system.com", password: "admin123")
3. Linked via winery_id foreign key

**Note:** Change default password on first login (future enhancement).

## Next steps
- ⏭️ Implement Phase 1: Core CRUD endpoints (6 endpoints, 15 tests)
- ⏭️ Implement Phase 2: Relationship endpoints (2 endpoints, 6 tests)
- ⏭️ Implement Phase 3: Seed script + documentation
- ⏭️ Future enhancements: Statistics endpoints, audit trail, bulk operations

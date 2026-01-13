# ADR-017: Winery API Design & REST Endpoints

**Status:** ✅ **Implemented**  
**Date Created:** January 13, 2026  
**Last Updated:** January 13, 2026 (Implemented)  
**Deciders:** AI Assistant + Álvaro (Product Owner)  
**Related ADRs:**
- ADR-016: Winery Service Layer (business logic ✅)
- ADR-002: Repository Architecture (data layer ✅)
- ADR-006: API Layer Design (pattern reference ✅)
- ADR-007: Authentication Module (JWT + RBAC ✅)
- ADR-025: Multi-Tenancy Security (winery_id enforcement ✅)
- ADR-026: Error Handling Strategy (domain errors ✅)
- ADR-027: Structured Logging (observability ✅)

---

## Context

The Winery module has complete **Repository** (44 tests) and **Service** (39 tests) layers implemented (ADR-016). **Authentication Module (ADR-007)** is fully operational with JWT, RBAC, and multi-tenancy. However, **there is no API Layer**, which means:

1. ❌ **No HTTP endpoints** to expose winery management functionality
2. ❌ **No Pydantic DTOs** for API requests/responses
3. ❌ **No OpenAPI documentation** (Swagger/ReDoc)
4. ❌ **No API integration tests** (TestClient)
5. ❌ **No FastAPI dependency injection** for services

**✅ PREREQUISITES COMPLETE:**
- ✅ **ADR-016**: WineryService implemented (9 methods, 39 tests)
- ✅ **ADR-007**: Auth module with JWT + RBAC
- ✅ **ADR-025**: Security strategy (winery_id enforcement)
- ✅ **ADR-026**: Error handling (domain errors ready)
- ✅ **ADR-027**: Structured logging (LoggingMiddleware)

**Key Challenge:**
Winery is a **TOP-LEVEL entity** (not scoped to winery_id like vineyards/fermentations). This requires:
- Admin-only namespace for most operations
- Special authorization logic (users can access only their own winery)
- Bootstrap/seed data for initial admin user

The system requires a REST API that:
- Exposes winery management operations (admin namespace)
- Integrates JWT authentication with RBAC
- Allows users to GET/UPDATE their own winery
- Restricts CREATE/DELETE to ADMIN role only
- Provides relationship endpoints (vineyards, fermentations)
- Supports seed data for initial winery creation

---

## Decision

### 1. API Layer Structure

```
src/modules/winery/src/api_component/
├── __init__.py
├── routers/
│   ├── __init__.py
│   └── winery_router.py                # Winery endpoints (admin namespace)
├── schemas/
│   ├── __init__.py
│   ├── requests/
│   │   ├── __init__.py
│   │   └── winery_requests.py          # Pydantic request DTOs
│   └── responses/
│       ├── __init__.py
│       └── winery_responses.py         # Pydantic response DTOs
├── dependencies/
│   ├── __init__.py
│   └── services.py                     # Service injection (DI)
└── error_handlers.py                   # HTTP error mapping
```

**Note:** Authentication dependencies (`get_current_user`, `require_admin`) come from `src/shared/auth/dependencies.py` (already implemented).

---

### 2. Endpoints Design

**Admin Namespace: `/api/v1/admin/wineries`**

Rationale: Winery is root entity (no winery_id scoping), most operations are admin-only.

**Core CRUD Endpoints (6):**
```
POST   /api/v1/admin/wineries              # Create winery (ADMIN only)
GET    /api/v1/admin/wineries/{id}         # Get winery by ID (users: own, ADMIN: all)
GET    /api/v1/admin/wineries/code/{code}  # Get winery by code (users: own, ADMIN: all)
GET    /api/v1/admin/wineries              # List wineries (ADMIN only)
PATCH  /api/v1/admin/wineries/{id}         # Update winery (users: own, ADMIN: all)
DELETE /api/v1/admin/wineries/{id}         # Soft delete winery (ADMIN only)
```

**Relationship Endpoints (2):**
```
GET    /api/v1/admin/wineries/{id}/vineyards      # List vineyards for winery
GET    /api/v1/admin/wineries/{id}/fermentations  # List fermentations for winery
```

**Total MVP Endpoints:** 8 endpoints (6 CRUD + 2 relationships)

---

### 3. Authorization Matrix

| Endpoint | ADMIN | WINEMAKER | Notes |
|----------|-------|-----------|-------|
| POST /wineries | ✅ | ❌ | System setup only |
| GET /wineries | ✅ | ❌ | List all wineries |
| GET /wineries/{id} | ✅ (all) | ✅ (own only) | Users see own winery |
| GET /wineries/code/{code} | ✅ (all) | ✅ (own only) | Lookup by code |
| PATCH /wineries/{id} | ✅ (all) | ✅ (own only) | Update details |
| DELETE /wineries/{id} | ✅ | ❌ | Soft delete with protection |
| GET /wineries/{id}/vineyards | ✅ (all) | ✅ (own only) | View relationships |
| GET /wineries/{id}/fermentations | ✅ (all) | ✅ (own only) | View relationships |

**Authorization Logic:**
```python
async def check_winery_access(winery_id: int, user: UserContext):
    """Allow ADMIN to access any winery, users can only access their own."""
    if user.role == "ADMIN":
        return  # Admin can access all wineries
    
    if user.winery_id != winery_id:
        raise HTTPException(status_code=403, detail="Access denied")
```

---

### 4. Request DTOs (Pydantic v2)

**WineryCreateRequest:**
```python
class WineryCreateRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50, description="Unique winery code")
    name: str = Field(..., min_length=1, max_length=200, description="Winery name")
    location: Optional[str] = Field(None, max_length=100, description="Geographic location")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @field_validator('code')
    def validate_code_format(cls, v):
        """Ensure code is alphanumeric with hyphens/underscores."""
        if not re.match(r'^[A-Z0-9_-]+$', v):
            raise ValueError('Code must be uppercase alphanumeric with hyphens/underscores')
        return v
```

**WineryUpdateRequest:**
```python
class WineryUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    location: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = None
    
    # Note: code is immutable (not allowed in updates)
```

---

### 5. Response DTOs (Pydantic v2)

**WineryResponse:**
```python
class WineryResponse(BaseModel):
    id: int
    code: str
    name: str
    location: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

**PaginatedWineriesResponse:**
```python
class PaginatedWineriesResponse(BaseModel):
    items: List[WineryResponse]
    total: int
    limit: int
    offset: int
```

**VineyardSummaryResponse** (for relationships):
```python
class VineyardSummaryResponse(BaseModel):
    id: int
    code: str
    name: str
    # Basic fields only (no deep nesting)
```

---

### 6. Error Handling

**HTTP Status Codes:**
- **200 OK**: Successful GET/PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Validation errors, business rule violations
- **401 Unauthorized**: Missing/invalid JWT token
- **403 Forbidden**: Insufficient permissions or cross-winery access attempt
- **404 Not Found**: Winery not found
- **409 Conflict**: Duplicate code or name
- **500 Internal Server Error**: Unexpected errors

**Error Response Format:**
```json
{
  "detail": "Winery with code BODEGA-001 already exists",
  "error_code": "DUPLICATE_CODE",
  "status_code": 409
}
```

---

### 7. Bootstrap & Seed Data

**Challenge:** First winery cannot be created without authenticated user, but users belong to wineries.

**Solution: Database Seed Script**
```python
# scripts/seed_initial_data.py
async def seed_initial_winery():
    """Create initial admin winery and user for system bootstrap."""
    # 1. Create initial winery
    winery = Winery(
        code="ADMIN-WINERY",
        name="System Administration Winery",
        location="System"
    )
    
    # 2. Create admin user linked to winery
    admin_user = User(
        email="admin@winery-system.com",
        password_hash=hash_password("admin123"),  # Change on first login
        role="ADMIN",
        winery_id=winery.id
    )
    
    # Run once during system setup
```

**Deployment:** Run seed script before API starts, or via migration.

---

### 8. Relationship Endpoints Design

**GET /admin/wineries/{id}/vineyards**
- Returns list of vineyards belonging to winery
- Uses VineyardRepository with winery_id filter
- Response: `List[VineyardSummaryResponse]`

**GET /admin/wineries/{id}/fermentations**
- Returns list of fermentations belonging to winery
- Uses FermentationRepository with winery_id filter
- Response: `List[FermentationSummaryResponse]`
- Optional filters: status, vintage_year, date_range

---

### 9. Implementation Phases

**Phase 1: Core CRUD (Priority: HIGH)**
- Create winery_router.py with 6 CRUD endpoints
- Implement request/response DTOs
- Create service dependency injection
- Write 15-20 API tests with TestClient
- Duration: 1-2 days

**Phase 2: Relationship Endpoints (Priority: MEDIUM)**
- Add vineyard listing endpoint
- Add fermentation listing endpoint
- Cross-module repository queries
- Write 5-8 relationship tests
- Duration: 1 day

**Phase 3: Seed Data & Documentation (Priority: HIGH)**
- Create seed script for initial winery
- Document bootstrap process
- Update API documentation
- Duration: 0.5 day

**Total Estimated Duration:** 2.5-3.5 days

---

## Consequences

### Positive
1. ✅ **Complete API coverage** for Winery module
2. ✅ **Admin namespace** clearly separates privileged operations
3. ✅ **Flexible authorization** (users access own winery, admins access all)
4. ✅ **Relationship navigation** enables cross-module queries
5. ✅ **Seed data strategy** solves bootstrap chicken-egg problem
6. ✅ **Consistent patterns** with Fruit Origin API (ADR-015)

### Negative
1. ⚠️ **Admin namespace** adds URL complexity (but necessary for security)
2. ⚠️ **Seed script required** for initial setup (but standard practice)
3. ⚠️ **Cross-module queries** for relationships (but well-scoped)

### Mitigations
- Provide clear documentation for seed script usage
- Use same auth patterns as other modules (consistency)
- Keep relationship endpoints simple (no deep nesting)

---

## Testing Strategy

**Approach:** Test-Driven Development (TDD)
- Write tests FIRST before implementation
- Red → Green → Refactor cycle
- Ensures 100% test coverage from day 1
- Tests serve as living documentation

### Unit Tests (Router Layer)
- Request DTO validation
- Authorization logic (admin vs user)
- Error response formatting
- Dependency injection mocking

### Integration Tests (API Layer)
**Core CRUD (15 tests):**
- Create winery (201) - success, duplicate code (409), validation errors (400)
- Get by ID (200) - success, not found (404), forbidden (403)
- Get by code (200) - success, not found (404), cross-winery blocked (403)
- List wineries (200) - pagination, admin-only (403)
- Update winery (200) - success, validation, immutable code, forbidden (403)
- Delete winery (204) - success, protection checks (400), admin-only (403)

**Relationships (6 tests):**
- List vineyards (200) - success, empty list, forbidden (403)
- List fermentations (200) - success, filtering, forbidden (403)

**Total:** 21 API tests (15 CRUD + 6 relationships)

---

## Open Questions

1. **Soft Delete Protection**: Should delete check for active users before allowing soft delete?
   - **Decision:** YES - WineryService.check_can_delete() already validates this
   
2. **List Endpoint Filtering**: Should regular users see their own winery in list endpoint?
   - **Recommendation:** Make list endpoint ADMIN-only for consistency
   
3. **Code Immutability**: Should code be updatable after creation?
   - **Decision:** NO - Code is business identifier (immutable like vineyard code)

---

## References

- **ADR-015**: Fruit Origin API (pattern reference)
- **ADR-016**: Winery Service Layer (business logic)
- **ADR-007**: Authentication Module (JWT + RBAC)
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Pydantic v2 Documentation**: https://docs.pydantic.dev/latest/

---

## Acceptance Criteria

1. ✅ 6 core CRUD endpoints implemented and tested
2. ✅ Authorization matrix enforced correctly (ADMIN + winery-scoped access)
3. ✅ 25 API tests passing (100% coverage)
4. ✅ OpenAPI documentation generated (auto via FastAPI)
5. 📋 Seed script (optional, not blocking)
6. ✅ No regressions in existing tests (79 module tests passing)
7. ✅ Consistent error handling with other modules (domain errors → HTTPException)
8. ✅ Integration with shared auth module (JWT + RBAC)

---

**Status:** ✅ IMPLEMENTED  
**Implementation Notes:**
- 6 endpoints: CREATE, GET (id), GET (code), LIST, UPDATE, DELETE
- 25 API tests: 6 CREATE + 8 GET + 3 LIST + 5 UPDATE + 3 DELETE
- Authorization: `require_admin` for CREATE/DELETE/LIST, `check_winery_access` for GET/UPDATE
- Error handling: IntegrityError, WineryNotFound, WineryNameAlreadyExists, InvalidWineryData
- Relationship endpoints (vineyards, fermentations) deferred to future iteration
**Blocked By:** None  
**Blocks:** None

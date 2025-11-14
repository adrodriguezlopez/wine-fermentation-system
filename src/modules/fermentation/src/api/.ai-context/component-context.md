# Component Context: API Layer (Fermentation Management Module)

> **Parent Context**: See `../../.ai-context/module-context.md` for module-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`
> **Related ADR**: [ADR-006: API Layer Design](../../../../.ai-context/adr/ADR-006-api-layer-design.md)

## Component responsibility
**HTTP REST API interface** for fermentation and sample management operations, providing authenticated and authorized access to business functionality.

**Position in module**: Presentation layer exposing HTTP endpoints with JWT authentication, request/response serialization, and multi-tenancy enforcement.

**Architectural Decision:** Following ADR-006, this component implements FastAPI routers with Pydantic v2 schemas, integrated with shared auth module (ADR-007) for JWT authentication and role-based access control.


## Architecture pattern
**RESTful API Pattern** with FastAPI framework and dependency injection.

**Design approach**: Clean separation between routers (endpoint definitions), schemas (request/response DTOs), and business logic (service layer), with auth dependencies injecting UserContext for multi-tenancy.

- **Routers**: fermentation_router (10 endpoints), sample_router (8 endpoints)
- **Request Schemas**: FermentationCreateRequest, FermentationUpdateRequest, SampleCreateRequest, SampleUpdateRequest (Pydantic v2)
- **Response Schemas**: FermentationResponse, SampleResponse, PaginatedResponse (Pydantic v2)
- **Authentication**: JWT token validation via `get_current_user` dependency from shared auth module
- **Authorization**: Role-based access control via `require_role` factory (ADMIN, WINEMAKER, OPERATOR, VIEWER)
- **Multi-tenancy**: Automatic winery_id filtering from UserContext extracted from JWT
- **Error Handling**: HTTP exception handlers mapping service errors to appropriate status codes
- **Data flow**: HTTP Request → Auth Middleware → Router → Service Layer → Response Serialization
- **Extension points**: Additional routers, custom validators, response transformers
- **Integration strategy**: Depends on service_component for business logic and shared/auth for authentication

## Component interfaces

### **Receives from (HTTP Clients)**
- **POST /api/v1/fermentations**: Create fermentation request with JWT token
- **GET /api/v1/fermentations/{id}**: Retrieve fermentation by ID
- **GET /api/v1/fermentations**: List fermentations with pagination/filtering
- **PATCH /api/v1/fermentations/{id}**: Update fermentation data
- **POST /api/v1/fermentations/{id}/samples**: Add sample to fermentation
- **GET /api/v1/samples/{id}**: Retrieve sample by ID
- **GET /api/v1/fermentations/{id}/samples**: List samples for fermentation
- **PATCH /api/v1/samples/{id}**: Update sample data

### **Provides to (HTTP Clients)**
- JSON responses with Pydantic serialization
- HTTP status codes: 200 (OK), 201 (Created), 400 (Validation Error), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 500 (Server Error)
- OpenAPI documentation: Swagger UI at /docs, ReDoc at /redoc
- Detailed validation error messages for client-side feedback

### **Uses (Internal Dependencies)**
- **Service Component**: FermentationService, SampleService for business logic
- **Auth Module** (shared/auth): `get_current_user`, `require_role` dependencies
- **Domain Entities**: For type hints and response serialization
- **Enums**: FermentationStatus, FermentationType, GrapeVariety for validation

## Key patterns implemented
- **RESTful API Design**: Resource-based URLs with standard HTTP methods
- **Dependency Injection**: FastAPI dependencies for auth, services, database sessions
- **Request/Response DTOs**: Pydantic schemas for validation and serialization
- **Authentication/Authorization**: JWT-based auth with role-based access control
- **Multi-tenancy**: Automatic winery_id enforcement from JWT token
- **Error Handling**: Consistent JSON error responses with HTTP status codes
- **API Versioning**: `/api/v1` prefix for future backward compatibility
- **OpenAPI**: Auto-generated documentation from Pydantic schemas

## Implementation status

### Phase 0: Setup ✅ (Completed Nov 8, 2025)
- [x] Branch created: `feature/fermentation-api-layer`
- [x] Directory structure: routers/, schemas/requests/, schemas/responses/
- [x] Component context documentation
- [x] Test infrastructure setup: conftest.py with enhanced fixtures ✅ **Updated Nov 14, 2025**
  - [x] `client`: FastAPI TestClient with real database session override
  - [x] `mock_user_context`: Mock UserContext for auth bypass
  - [x] `override_db_session`: Session-scoped SQLite for all tests (shared cache)
  - [x] `test_db_session`: Function-scoped session with data cleanup
  - [x] Database initialization via `initialize_database()` and `get_db_session()`
  - [x] FastAPI dependency overrides for both auth and database
  - [x] aiosqlite dependency added
  - [x] All fixture tests passing

### Phase 1: Schemas (In Progress - Nov 8, 2025)
- [x] Response schemas (FermentationResponse, SampleResponse) ✅
  - [x] `FermentationResponse` with Pydantic v2 validation
  - [x] `SampleResponse` with Pydantic v2 validation
  - [x] `from_entity()` class method for entity conversion
  - [x] JSON serialization support (model_dump, model_dump_json)
  - [x] Field constraints and optional field handling
  - [x] 6/6 tests passing (test_response_schemas.py)
- [x] Request schemas (FermentationCreateRequest, UpdateRequest, etc.) ✅ **Completed Nov 8, 2025**
  - [x] `FermentationCreateRequest` with required field validation
  - [x] `FermentationUpdateRequest` with all optional fields (partial updates)
  - [x] `SampleCreateRequest` with required field validation
  - [x] `SampleUpdateRequest` with optional fields
  - [x] Field constraints: ranges (ge, le, gt), string lengths (min/max_length)
  - [x] 10/10 tests passing (test_request_schemas.py)

### Phase 2: Fermentation Endpoints (In Progress - Nov 14, 2025)
- [x] POST /api/v1/fermentations (create) ✅ **Completed Nov 14, 2025**
  - [x] Real PostgreSQL database integration via FastAPI dependencies
  - [x] JWT authentication with `require_winemaker` dependency
  - [x] Multi-tenancy enforcement (winery_id from UserContext)
  - [x] Request validation with Pydantic schemas
  - [x] Service layer integration (FermentationService)
  - [x] 15/15 endpoint tests passing
- [x] GET /api/v1/fermentations/{id} (read) ✅ **Completed Nov 14, 2025**
  - [x] Real PostgreSQL database integration
  - [x] JWT authentication with `get_current_user` dependency
  - [x] Multi-tenancy check (returns 404 for wrong winery)
  - [x] 14/14 endpoint tests passing
- [ ] GET /api/v1/fermentations (list with pagination)
- [ ] PATCH /api/v1/fermentations/{id} (update)
- **Tests: 29/~45 passing (64%)**

### Phase 3: Sample Endpoints (Not Started)
- [ ] POST /api/v1/fermentations/{id}/samples (create)
- [ ] GET /api/v1/samples/{id} (read)
- [ ] GET /api/v1/fermentations/{id}/samples (list)
- [ ] PATCH /api/v1/samples/{id} (update)
- [ ] Endpoint tests (~20 tests)

### Phase 4: Integration (Not Started)
- [ ] End-to-end API flow tests
- [ ] OpenAPI documentation validation
- [ ] Error handler middleware
- [ ] Performance testing
- [ ] API README documentation

## Testing strategy
**Test-Driven Development (TDD)** with Red-Green-Refactor cycle.

### Test Infrastructure ✅ (Completed)
- **TestClient**: FastAPI TestClient for HTTP testing ✅
- **Mock Authentication**: Override auth dependencies for isolated testing ✅
- **Test Database**: SQLite in-memory for integration tests ✅
- **Mock Services**: Service layer mocks for unit testing endpoints (pending)

### Test Progress
**Completed:**
- ✅ `tests/api/conftest.py` - Infrastructure tests passing
  - test_client_fixture_exists
  - test_mock_user_context_fixture
  - test_test_db_fixture
- ✅ `tests/api/test_response_schemas.py` - 6 schema tests passing
  - test_fermentation_response_from_entity
  - test_fermentation_response_json_serialization
  - test_fermentation_response_optional_vessel_code
  - test_sample_response_from_entity
  - test_sample_response_json_serialization
  - test_fermentation_response_validation_error
- ✅ `tests/api/test_request_schemas.py` - 10 schema tests passing
  - test_fermentation_create_request_valid_data
  - test_fermentation_create_request_missing_required_fields
  - test_fermentation_create_request_invalid_ranges
  - test_fermentation_create_request_optional_vessel_code
  - test_fermentation_update_request_partial_updates
  - test_fermentation_update_request_all_optional
  - test_sample_create_request_valid_data
  - test_sample_create_request_missing_fields
  - test_sample_create_request_string_length
  - test_sample_update_request_partial
- ✅ `tests/api/test_fermentation_endpoints.py` - 29 endpoint tests passing ✅ **NEW Nov 14, 2025**
  - **TestPostFermentations** (15 tests):
    - test_create_fermentation_success
    - test_create_fermentation_returns_201_status
    - test_create_fermentation_includes_location_header
    - test_create_fermentation_without_authentication
    - test_create_fermentation_viewer_forbidden
    - test_create_fermentation_operator_forbidden
    - test_create_fermentation_missing_required_fields
    - test_create_fermentation_invalid_data_types
    - test_create_fermentation_invalid_date
    - test_create_fermentation_duplicate_vessel_code
    - test_create_fermentation_invalid_ranges
    - test_create_fermentation_uses_auth_user_winery
    - test_create_fermentation_sets_initial_status_active
    - test_create_fermentation_persists_to_database
    - test_create_fermentation_service_error_500
  - **TestGetFermentationEndpoint** (14 tests):
    - test_get_fermentation_success
    - test_get_fermentation_not_found
    - test_get_fermentation_wrong_winery
    - test_get_fermentation_without_authentication
    - test_get_fermentation_unauthorized_role (VIEWER can read)

**Total: 48/~79 tests passing (61%)** ✅ **Updated Nov 14, 2025**

### Test Categories
1. **Schema Tests** (16/16 completed) ✅:
   - ✅ Response serialization (entity to DTO conversion)
   - ✅ JSON serialization (model_dump, model_dump_json)
   - ✅ Optional field handling
   - ✅ Pydantic validation errors
   - ✅ Request validation (required fields, data types, ranges)
   - ✅ Partial updates (all fields optional)
   - ✅ String length validation (min_length, max_length)
   - ✅ Numeric range validation (ge, le, gt)

2. **Endpoint Tests** (29/~45 completed, 64%) ✅ **In Progress Nov 14, 2025**:
   - ✅ POST /fermentations: 15/15 tests passing
     - ✅ Successful creation with real database
     - ✅ Authentication required (401 without token)
     - ✅ Authorization required (403 for viewer/operator)
     - ✅ Multi-tenancy enforcement
     - ✅ Request validation errors
     - ✅ Business rule violations
     - ✅ Unique vessel code constraint
   - ✅ GET /fermentations/{id}: 14/14 tests passing
     - ✅ Successful retrieval
     - ✅ Not found (404)
     - ✅ Multi-tenancy check (404 for wrong winery)
     - ✅ Authentication required
     - ✅ Viewer role can read (ADR-006)
   - [ ] GET /fermentations (list): 0/8 pending
   - [ ] PATCH /fermentations/{id}: 0/8 pending

3. **Integration Tests** (0/~15):
   - End-to-end flows: Create → Read → Update → Delete
   - Cross-endpoint interactions
   - Database transactions
   - Error handling

### Running Tests
```bash
# All API tests
poetry run pytest tests/api/ -v

# Specific test files
poetry run pytest tests/api/test_response_schemas.py -v

# With coverage
poetry run pytest tests/api/ --cov=src/modules/fermentation/src/api --cov-report=html
```

## Dependencies

### External Libraries
- **FastAPI** (>=0.104.0): Web framework
- **Pydantic** (v2): Schema validation and serialization
- **Uvicorn**: ASGI server for development

### Internal Dependencies
- **shared/auth**: JWT authentication and authorization
  - `get_current_user()`: Extract UserContext from JWT
  - `require_winemaker()`: Shortcut for ADMIN/WINEMAKER roles
  - `require_role()`: Role-based access control factory
  - `UserContext`: JWT claims with user_id, winery_id, role
- **shared/infra/database**: Database session management ✅ **NEW Nov 14, 2025**
  - `get_db_session()`: FastAPI dependency providing AsyncSession
  - `initialize_database()`: Setup database configuration
  - `DatabaseConfig`: PostgreSQL/SQLite configuration
  - `FastAPISessionManager`: ISessionManager wrapper for repositories
- **service_component**: Business logic layer
  - `FermentationService`: 7 fermentation operations
  - `SampleService`: 6 sample operations
- **repository_component**: Data persistence layer ✅ **NEW Nov 14, 2025**
  - `FermentationRepository`: Database operations via ISessionManager
  - Real PostgreSQL integration in production
  - SQLite in-memory for testing
- **domain**: Entities and enums for type hints
  - `Fermentation`, `Sample`, `User` entities
  - `FermentationStatus`, `FermentationType` enums

## Error handling

### HTTP Status Code Mapping
- **200 OK**: Successful GET, PATCH operations
- **201 Created**: Successful POST operations
- **400 Bad Request**: Pydantic validation errors, business rule violations
- **401 Unauthorized**: Missing token, invalid token, expired token
- **403 Forbidden**: Insufficient permissions (role-based), multi-tenancy violation
- **404 Not Found**: Resource not found (fermentation, sample)
- **500 Internal Server Error**: Unexpected service errors

### Error Response Format
```json
{
  "detail": "Error message description",
  "error_type": "ValidationError",
  "errors": [
    {
      "field": "start_date",
      "message": "Start date must be before end date"
    }
  ]
}
```

## Security considerations

### Authentication
- **JWT Tokens**: HS256 algorithm, 15-minute access token expiry
- **Token Validation**: Signature verification, expiration check, claims extraction
- **Bearer Scheme**: `Authorization: Bearer <token>` header required

### Authorization
- **Role-Based Access Control**:
  - CREATE/UPDATE/DELETE: ADMIN, WINEMAKER only
  - READ: All authenticated users
  - Sample CREATE: ADMIN, WINEMAKER, OPERATOR
- **Permission Matrix**: Defined in ADR-007

### Multi-tenancy
- **Automatic Filtering**: winery_id from JWT token enforced on all queries
- **Creation Enforcement**: winery_id auto-set on resource creation
- **Cross-Winery Prevention**: 403 Forbidden on access attempts to other wineries' data

### Input Validation
- **Pydantic Validation**: Type checking, range validation, required fields
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy
- **XSS Prevention**: JSON serialization escapes HTML/JS

## Future enhancements
- [ ] Rate limiting per user/winery
- [ ] API key authentication for service-to-service
- [ ] GraphQL endpoint for complex queries
- [ ] WebSocket support for real-time sample updates
- [ ] Bulk operations (batch create/update)
- [ ] Export endpoints (CSV, PDF reports)
- [ ] API usage analytics and monitoring
- [ ] Response compression (gzip)
- [ ] CORS configuration for web clients
- [ ] API gateway integration

## References
- [ADR-006: API Layer Design](../../../../.ai-context/adr/ADR-006-api-layer-design.md)
- [ADR-007: Auth Module Design](../../../../.ai-context/adr/ADR-007-auth-module-design.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [OpenAPI Specification](https://swagger.io/specification/)

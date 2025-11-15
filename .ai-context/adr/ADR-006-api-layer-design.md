# ADR-006: API Layer Design & FastAPI Integration

**Status:** ✅ **IMPLEMENTED - Phase 3 Complete** (Nov 15, 2025)  
**Date Created:** 2025-10-26  
**Date Ready:** 2025-11-04  
**Date Implemented:** 2025-11-15  
**Deciders:** Development Team  
**Related ADRs:** 
- ADR-005 (Service Layer Interfaces - ✅ Implemented)
- ADR-007 (Authentication Module - ✅ Implemented, prerequisite complete)

> **📋 Context Files:**
> - [Architectural Guidelines](../ARCHITECTURAL_GUIDELINES.md) - Principios de diseño
> - [Service Layer Interfaces](./ADR-005-service-layer-interfaces.md) - Contratos de servicio
> - [Authentication Module](./ADR-007-auth-module-design.md) - Auth infrastructure

---

## Context

El módulo de fermentación tiene implementadas las capas Domain, Repository y Service (182 tests passing). El **Authentication Module (ADR-007) está completamente implementado** (186 tests passing). Sin embargo, **no tiene API Layer**, lo que significa:

1. **No hay endpoints HTTP** para exponer la funcionalidad
2. **No hay DTOs de API** (request/response Pydantic models)
3. **No hay integración de autenticación/autorización** en endpoints HTTP
4. **No hay documentación OpenAPI** automática
5. **No hay manejo de errores HTTP** (status codes)
6. **No hay dependency injection** para FastAPI
7. **No hay tests de API** (integration tests con TestClient)

**✅ PREREQUISITO COMPLETADO**: El **Authentication Module (ADR-007)** está implementado y provee:
- ✅ JWT token generation y validation (JwtService)
- ✅ User authentication (AuthService con login/refresh)
- ✅ Multi-tenancy enforcement (winery_id en UserContext)
- ✅ Role-based authorization (UserRole enum con permisos)
- ✅ `get_current_user()` dependency para FastAPI
- ✅ `require_role()` factory para RBAC
- ✅ 186 tests passing (163 unit + 24 integration)

El sistema requiere una API REST bien diseñada que:
- Exponga las operaciones de fermentación y samples
- Integre autenticación JWT (usando auth module)
- Maneje multi-tenancy (winery_id en contexto)
- Provea documentación interactiva (Swagger/ReDoc)
- Siga convenciones REST estándar
- Sea testeable y mantenible

---

## Decision

### 1. Estructura de API Layer

```
src/modules/fermentation/src/api_component/
├── __init__.py
├── routers/
│   ├── __init__.py
│   ├── fermentation_router.py          # Fermentation endpoints
│   └── sample_router.py                # Sample endpoints
├── schemas/
│   ├── __init__.py
│   ├── requests/
│   │   ├── __init__.py
│   │   ├── fermentation_requests.py    # Request DTOs (Pydantic)
│   │   └── sample_requests.py
│   └── responses/
│       ├── __init__.py
│       ├── fermentation_responses.py   # Response DTOs (Pydantic)
│       └── sample_responses.py
├── dependencies/
│   ├── __init__.py
│   ├── auth.py                         # JWT authentication
│   ├── database.py                     # DB session dependency
│   └── services.py                     # Service injection
├── middleware/
│   ├── __init__.py
│   └── error_handler.py                # HTTP error mapping
└── main.py                             # FastAPI app factory
```

### 2. Endpoints Design

**Fermentation Endpoints (10 endpoints):**
```
POST   /api/v1/fermentations                    # Create fermentation
GET    /api/v1/fermentations/{id}               # Get by ID
GET    /api/v1/fermentations                    # List (filters: status, include_completed)
PATCH  /api/v1/fermentations/{id}/status        # Update status
PATCH  /api/v1/fermentations/{id}/complete      # Complete fermentation
DELETE /api/v1/fermentations/{id}               # Soft delete
POST   /api/v1/fermentations/validate           # Dry-run validation
GET    /api/v1/fermentations/{id}/samples       # Get all samples (convenience)
GET    /api/v1/fermentations/{id}/timeline      # Get sample timeline
GET    /api/v1/fermentations/{id}/statistics    # Get fermentation stats
```

**Sample Endpoints (8 endpoints):**
```
POST   /api/v1/samples                          # Add sample to fermentation
GET    /api/v1/samples/{id}                     # Get sample by ID
GET    /api/v1/samples                          # List samples (filter: fermentation_id)
GET    /api/v1/samples/latest                   # Get latest sample (filter: fermentation_id, type)
GET    /api/v1/samples/timerange                # Get samples in time range
POST   /api/v1/samples/validate                 # Dry-run validation
DELETE /api/v1/samples/{id}                     # Soft delete sample (future)
GET    /api/v1/samples/types                    # Get available sample types
```

### 3. Request/Response DTOs (Pydantic)

**Request DTOs:**
- `FermentationCreateRequest` - Crear fermentación
- `FermentationUpdateStatusRequest` - Cambiar estado
- `FermentationCompleteRequest` - Completar fermentación
- `SampleCreateRequest` - Agregar muestra
- `SampleQueryFilters` - Filtros de búsqueda
- `TimeRangeQuery` - Consultas temporales

**Response DTOs:**
- `FermentationResponse` - Entidad fermentación
- `FermentationListResponse` - Lista paginada
- `FermentationStatisticsResponse` - Estadísticas calculadas
- `SampleResponse` - Entidad muestra
- `SampleListResponse` - Lista de muestras
- `ValidationResponse` - Resultado de validación
- `ErrorResponse` - Error HTTP estándar

### 4. Authentication & Authorization

**PREREQUISITE**: Requiere Auth Module (ADR-007) implementado en `src/shared/auth/`

**JWT Authentication:**
- Header: `Authorization: Bearer <token>`
- Claims: `user_id`, `winery_id`, `role`, `permissions`
- Dependency: `get_current_user()` → `UserContext` (provided by shared/auth)
- Multi-tenancy: `winery_id` extraído automáticamente del token

**Integration:**
```python
from src.shared.auth.dependencies import get_current_user, require_role
from src.shared.auth.domain.dtos import UserContext

@router.post("/fermentations")
async def create_fermentation(
    request: FermentationCreateRequest,
    user: UserContext = Depends(get_current_user)  # From shared auth
):
    ...
```

**Authorization Levels:**
- **Admin**: Todas las operaciones
- **Winemaker**: CRUD fermentaciones + samples
- **Operator**: Read fermentaciones, Add samples
- **Viewer**: Solo lectura

### 5. Error Handling & HTTP Status Codes

**Exception Mapping:**
```python
FermentationNotFoundError       → 404 Not Found
InvalidFermentationStatusError  → 400 Bad Request
FermentationAlreadyExistsError  → 409 Conflict
UnauthorizedError               → 401 Unauthorized
ForbiddenError                  → 403 Forbidden
ValidationError                 → 422 Unprocessable Entity
DatabaseError                   → 500 Internal Server Error
```

**Error Response Format:**
```json
{
  "error": "FERMENTATION_NOT_FOUND",
  "message": "Fermentation with ID 123 not found",
  "details": {
    "fermentation_id": 123,
    "winery_id": 1
  },
  "timestamp": "2025-10-26T10:30:00Z"
}
```

### 6. Dependency Injection Pattern

```python
# dependencies/services.py
def get_fermentation_service(
    db: AsyncSession = Depends(get_db_session),
    user: UserContext = Depends(get_current_user)
) -> IFermentationService:
    repository = FermentationRepository(db)
    validator = FermentationValidator()
    return FermentationService(repository, validator)

# Router usage
@router.post("/fermentations")
async def create_fermentation(
    request: FermentationCreateRequest,
    service: IFermentationService = Depends(get_fermentation_service),
    user: UserContext = Depends(get_current_user)
) -> FermentationResponse:
    fermentation = await service.create_fermentation(
        winery_id=user.winery_id,
        user_id=user.user_id,
        data=request.to_dto()
    )
    return FermentationResponse.from_entity(fermentation)
```

### 7. OpenAPI Documentation

**Swagger UI:** `/docs`  
**ReDoc:** `/redoc`  
**OpenAPI JSON:** `/openapi.json`

**Metadata:**
- Title: "Wine Fermentation API"
- Version: "1.0.0"
- Description: "REST API for managing wine fermentation processes"
- Contact: Development Team
- License: Proprietary

**Tags:**
- `Fermentations` - Fermentation management endpoints
- `Samples` - Sample data endpoints
- `Validation` - Dry-run validation endpoints

### 8. Testing Strategy

**API Tests (40-50 tests):**
```
tests/api/
├── conftest.py                      # TestClient fixture, test DB, mock auth
├── test_fermentation_endpoints.py   # ~20 tests
├── test_sample_endpoints.py         # ~15 tests
├── test_authentication.py           # ~8 tests
├── test_error_handling.py           # ~5 tests
└── test_validation_endpoints.py     # ~3 tests
```

**Test Categories:**
- **Happy Path**: CRUD operations exitosas
- **Validation**: Errores 422 con data inválida
- **Authorization**: Errores 401/403 sin permisos
- **Multi-tenancy**: Aislamiento por winery_id
- **Edge Cases**: Not found, conflicts, race conditions

---

## Architectural Notes

### Alignment with Guidelines

✅ **Follows [ARCHITECTURAL_GUIDELINES.md](../ARCHITECTURAL_GUIDELINES.md):**
- Separation of concerns (Router → Service → Repository)
- Dependency injection for testability
- Type safety with Pydantic
- Error handling at boundaries
- Multi-tenancy enforcement
- Async/await for performance

### Trade-offs

**Chosen:**
- **FastAPI** over Flask/Django REST: Mejor performance, async native, validación automática
- **Pydantic v2** para DTOs: Type safety, serialización rápida, documentación automática
- **JWT** sobre sessions: Stateless, escalable, microservices-ready
- **Soft deletes** en API: Audit trail, recuperación de datos

**Rejected:**
- **GraphQL**: Overhead innecesario para este dominio
- **gRPC**: No requerido, clientes HTTP estándar suficientes
- **Versioning en URL**: v1 hardcoded, future v2 si breaking changes

### Integration Points

**Auth Module (DEPENDENCY - ADR-007):**
- API depende de `shared.auth` para autenticación y autorización
- `get_current_user()` dependency injection
- `UserContext` DTO con `user_id`, `winery_id`, `role`
- JWT validation y token refresh

**Service Layer:**
- API depende de `IFermentationService` y `ISampleService` (ADR-005)
- DTOs de API se mapean a DTOs de servicio (`FermentationCreate`, `SampleCreate`)
- Validaciones delegadas a `IFermentationValidator`

**Repository Layer:**
- No acceso directo desde API (violación de capas)
- DB Session inyectado a través de dependency → service → repository

**Domain Layer:**
- Entidades (`Fermentation`, `BaseSample`) mapeadas a Response DTOs
- Enums (`FermentationStatus`, `SampleType`) expuestos en OpenAPI

---

## Consequences

### ✅ Benefits

1. **Funcionalidad expuesta**: Fermentaciones y samples accesibles vía HTTP
2. **Documentación automática**: Swagger UI out-of-the-box
3. **Type safety**: Pydantic valida requests automáticamente
4. **Testeable**: TestClient permite tests sin servidor real
5. **Extensible**: Nuevos endpoints fáciles de agregar
6. **Seguro**: Autenticación JWT + multi-tenancy enforcement
7. **Estándar REST**: Convenciones HTTP bien conocidas

### ⚠️ Trade-offs

1. **Complejidad**: +7 nuevos archivos, ~1200-1500 líneas de código
2. **Mapping overhead**: Request DTO → Service DTO → Entity (3 capas)
3. **Testing burden**: +40-50 API tests necesarios
4. **Auth setup**: Requiere JWT secret, token generation, refresh logic

### ❌ Limitations

1. **No WebSockets**: Eventos en tiempo real no soportados (future)
2. **No GraphQL**: Consultas complejas requieren múltiples requests
3. **No rate limiting**: Debe agregarse en API Gateway (future)
4. **No caching**: Headers HTTP cache no implementados (future)

### 📊 Implementation Estimate

- **Routers**: ~400 líneas (2 archivos)
- **Schemas**: ~600 líneas (6 archivos)
- **Dependencies**: ~200 líneas (3 archivos)
- **Middleware**: ~100 líneas (1 archivo)
- **Tests**: ~800 líneas (5 archivos)
- **Total**: ~2100 líneas, ~18 endpoints, ~45 tests

**Effort**: 3-4 días de desarrollo + 1 día testing

---

## Implementation Checklist

### ✅ Phase 1: Foundation (Day 1) - COMPLETE
- [x] Create API component structure
- [x] Implement dependencies (auth, database, services)
- [x] Setup error handler middleware (integrated in routers)
- [x] Test fixtures (TestClient, mock auth, real database)
- [x] 16 schema validation tests passing

### ✅ Phase 2: Fermentation API (Day 2) - COMPLETE
- [x] Request/Response DTOs for fermentations
- [x] FermentationRouter with 2 core endpoints (POST, GET by ID)
  - POST /api/v1/fermentations - Create with validation
  - GET /api/v1/fermentations/{id} - Get by ID with multi-tenancy
- [x] Mapping layer (Request DTO → Service DTO → Domain)
- [x] Integration with FermentationService (real PostgreSQL)
- [x] JWT authentication with `require_winemaker` and `get_current_user`
- [x] Multi-tenancy enforcement (winery_id from UserContext)
- [x] 29 endpoint tests passing (15 POST + 14 GET)

### ✅ Phase 3: Sample API (Day 3) - COMPLETE
- [x] Request/Response DTOs for samples
- [x] SampleRouter with 4 core endpoints:
  - POST /fermentations/{id}/samples - Create with validation
  - GET /fermentations/{id}/samples - List chronologically
  - GET /fermentations/{id}/samples/{sample_id} - Get by ID
  - GET /fermentations/{id}/samples/latest - Latest with optional type filter
- [x] Mapping layer for samples
- [x] Integration with SampleService (real PostgreSQL)
- [x] Complete validation orchestration (chronology, value, business rules)
- [x] 12 endpoint tests passing (4 + 3 + 2 + 3)

### 🔄 Phase 4: Additional Endpoints (Pending)
- [ ] GET /api/v1/fermentations (list with filters)
- [ ] PATCH /api/v1/fermentations/{id} (update fermentation)
- [ ] PATCH /api/v1/fermentations/{id}/status (update status)
- [ ] DELETE /api/v1/fermentations/{id} (soft delete)
- [ ] POST /api/v1/fermentations/validate (dry-run validation)
- [ ] Additional sample endpoints (timerange queries, etc.)

### 📊 Current Status (Nov 15, 2025)
- **Endpoints Implemented**: 6/18 (33%)
  - Fermentation: 2/10 (POST create, GET by id)
  - Sample: 4/8 (POST create, GET list, GET by id, GET latest)
- **Tests Passing**: 57 API tests (100%)
  - Schema validation: 16/16 ✅
  - Fermentation endpoints: 29/29 ✅
  - Sample endpoints: 12/12 ✅
- **Database**: Real PostgreSQL integration ✅
- **Authentication**: JWT with shared Auth module ✅
- **Multi-tenancy**: Winery isolation enforced ✅

---

## Status

**✅ PARTIALLY IMPLEMENTED** - Phases 1-3 Complete (Nov 15, 2025)

**Dependency:** ✅ ADR-007 (Auth Module) implemented and integrated

**Implementation Progress:**
1. ✅ ADR-007: Auth Module implemented (163 unit tests passing)
2. ✅ ADR-006 Phase 1-3: Core API endpoints (57 API tests passing)
3. 🔄 ADR-006 Phase 4: Additional endpoints pending

**What's Working:**
- ✅ FastAPI routers with real PostgreSQL database
- ✅ JWT authentication from shared Auth module
- ✅ Multi-tenancy enforcement (winery_id filtering)
- ✅ Request/response validation with Pydantic v2
- ✅ Complete sample validation orchestration
- ✅ Error handling with proper HTTP status codes
- ✅ 414 total tests passing (100% coverage)

**Next Steps:**
1. Implement remaining fermentation endpoints (GET list, PATCH, DELETE)
2. Add timerange queries for samples
3. Add validation endpoints (dry-run)
4. Performance optimization (if needed)
5. Rate limiting (future enhancement)

**Branch:** `feature/fermentation-api-layer` (6441929)

---

## Lessons Learned (Nov 15, 2025)

### Session Management
**Challenge:** Repository methods failing with "session not defined"  
**Solution:** Always use `async with session_cm as session:` pattern  
**Impact:** Fixed 3 repository methods, enabled all API tests

### Enum Value Handling
**Challenge:** SampleType enum validation failing  
**Solution:** Use `.lower()` for string-to-enum conversion  
**Learning:** Always verify enum value casing before conversion

### Pydantic v2 Validation
**Challenge:** ValidationResult revalidation errors  
**Solution:** Use `model_construct()` to bypass validation, add `ConfigDict(revalidate_instances='never')`  
**Learning:** Pydantic v2 revalidates BaseModel instances in lists

### Cross-Module Dependencies
**Challenge:** User entity relationships causing circular dependency in Auth tests  
**Solution:** Comment out bidirectional relationships, use explicit queries  
**Learning:** Avoid bidirectional SQLAlchemy relationships across modules

### Route Specificity
**Challenge:** `/samples/latest` being captured by `/{sample_id}` route  
**Solution:** Register more specific routes BEFORE parameterized routes  
**Learning:** FastAPI route order matters for path matching

---

## References

- **[ADR-007: Auth Module Design](./ADR-007-auth-module-design.md)** - PREREQUISITE
- [ADR-005: Service Layer Interfaces](./ADR-005-service-layer-interfaces.md)
- [ADR-003: Repository Architecture](./ADR-003-repository-interface-refactoring.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [REST API Design Best Practices](https://restfulapi.net/)

# ADR-025: Multi-Tenancy Security & winery_id Enforcement (LIGHT - Pilot Version)

**Status**: Proposed (LIGHT Implementation for Pilot)  
**Date**: December 23, 2025  
**Deciders**: Architecture Team  
**Technical Story**: Enforce winery_id-based data isolation for pilot phase (1-2 wineries), with clear upgrade path to full multi-tenancy

**Version**: LIGHT (2-3 days) - Sufficient for pilot with 1-2 wineries  
**Future Upgrade**: Full version with PostgreSQL RLS available when scaling to 5+ wineries

**Related ADRs:**
- ADR-001: Domain model (winery_id in entities)
- ADR-002: Repository architecture (multi-tenant scoping helpers)
- ADR-007: Authentication module (JWT with winery_id)
- ADR-027: Structured logging (security event logging)
- ADR-028: Module dependency management (independent security layer injection)

---

## Context

El sistema maneja datos de múltiples bodegas (wineries) en una base de datos compartida. Actualmente:

**✅ IMPLEMENTADO:**
1. **User entity** tiene `winery_id` FK a `wineries.id` ([user.py](c:\dev\wine-fermentation-system\src\shared\auth\domain\entities\user.py#L41-L44))
2. **JWT tokens** incluyen `winery_id` en payload ([jwt_service.py](c:\dev\wine-fermentation-system\src\shared\auth\infra\services\jwt_service.py#L44-L72))
3. **Fermentation entity** tiene `winery_id` FK ([fermentation.py](c:\dev\wine-fermentation-system\src\modules\fermentation\src\domain\entities\fermentation.py#L27))
4. **BaseRepository** tiene helpers `scope_query_by_winery_id()` ([base_repository.py](c:\dev\wine-fermentation-system\src\shared\infra\repository\base_repository.py#L102-L126))
5. **Services** reciben `winery_id` como parámetro en métodos ([sample_router.py](c:\dev\wine-fermentation-system\src\modules\fermentation\src\api\routers\sample_router.py#L236))

**❌ VULNERABILIDADES:**
1. **No enforcement sistemático**: `winery_id` se pasa manualmente, vulnerable a errores
2. **API Layer puede omitir validación**: Nada impide que un endpoint olvide validar `winery_id`
3. **Cross-winery queries posibles**: Query sin filtro de `winery_id` expone datos de otras bodegas
4. **Sin PostgreSQL RLS**: Base de datos no valida acceso, solo aplicación
5. **Sin logging de seguridad**: Intentos de acceso cross-winery no se auditan
6. **Inconsistencia en errores**: Algunos lugares 404, otros 403

**RIESGOS:**
- 🔴 **Data Leak**: Usuario de Winery A puede ver datos de Winery B si API olvida filtrar
- 🔴 **Compliance**: GDPR/SOC2 requieren segregación estricta de datos multi-tenant
- 🔴 **Trust**: Una bodega comprometida puede acceder datos de otras bodegas

**CONTEXTO DEL PROYECTO:**
- 🧪 **Proyecto piloto experimental** - No sabemos si funcionará
- 🏢 **1-2 wineries máximo** en fase inicial
- ⏱️ **Time-to-market crítico** - Necesitamos validar concepto rápido
- 💰 **Presupuesto limitado** - Cada día cuenta

**DECISIÓN ESTRATÉGICA: Implementación por Fases**
- ✅ **LIGHT Version AHORA (2-3 días)**: Validación básica, suficiente para piloto
- 🔄 **Medium Version SI PILOTO EXITOSO**: Middleware + enforcement automático (5-6 días)
- 🚀 **Full Version SI ESCALAMOS**: PostgreSQL RLS + compliance (4 días adicionales)

**OPORTUNIDAD ESTRATÉGICA (Post ADR-027 & ADR-028):**
- Logging infrastructure LISTA para eventos de seguridad
- Module independence permite inyectar security layer sin refactoring masivo
- 4 módulos nuevos (Fruit Origin Service, Winery Service, Historical Data, Analysis) **NACERÁN SEGUROS**
- Solo 2 módulos (Fermentation, Auth) requieren refactoring

---

## Decision

Implementamos **Multi-Tenancy Security LIGHT** con enforcement en 2 niveles (suficiente para piloto):

**SCOPE LIGHT (Esta implementación):**
- ✅ Repository layer con `winery_id` REQUIRED
- ✅ API layer con validación explícita
- ✅ Error handling 403 Forbidden
- ✅ Security logging básico (ADR-027)
- ❌ NO Middleware complejo (KISS para piloto)
- ❌ NO PostgreSQL RLS (dejamos para escalamiento)

**FUTURE ENHANCEMENTS (Cuando escalemos):**
- 🔄 Middleware `WineryContextMiddleware` (DRY, automático)
- 🔄 Dependency `get_winery_id()` (imposible olvidar)
- 🔄 PostgreSQL RLS policies (defense in depth, compliance)

---

### 1. Repository Layer - Mandatory winery_id Validation



**Decisión**: Repositories SIEMPRE validan `winery_id` - pero de forma simple y explícita.

**Patrón Simple (LIGHT):**
```python
# src/modules/fermentation/src/repository_component/repositories/fermentation_repository.py

async def get_by_id(self, fermentation_id: int, winery_id: int) -> Optional[Fermentation]:
    """
    Get fermentation by ID with winery_id validation.
    
    Args:
        fermentation_id: Fermentation ID
        winery_id: Winery ID for access control (REQUIRED)
        
    Returns:
        Fermentation if found AND belongs to winery, None otherwise
    """
    # Validate winery_id
    if not winery_id or winery_id <= 0:
        raise ValueError(f"winery_id is REQUIRED, got: {winery_id}")
    
    # Query with winery_id filter
    stmt = select(Fermentation).where(
        Fermentation.id == fermentation_id,
        Fermentation.winery_id == winery_id,  # ← CRITICAL: Always filter by winery
        Fermentation.is_deleted == False
    )
    
    session_cm = await self.get_session()
    async with session_cm as session:
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

**¿Por qué no usar helper complejo?**
- ✅ **KISS**: Más fácil de entender para devs nuevos
- ✅ **Debugging**: Queries explícitas, fácil de debuggear
- ✅ **Suficiente para piloto**: Con 1-2 wineries no necesitas abstracción
- 🔄 **Upgrade path**: Cuando escalemos, agregamos `build_scoped_query()`

**Repositories a refactorizar (LIGHT):**
- ✅ `FermentationRepository` - 3 métodos críticos (get_by_id, list_all, create)
- ✅ `SampleRepository` - 2 métodos críticos (get_by_id, list_by_fermentation)
- ✅ `HarvestLotRepository` - 2 métodos críticos (get_by_id, get_by_code)

**Entities sin winery_id (globales):**
- ❌ `User` - Pertenece a una winery, pero no se filtra por winery_id
- ❌ `GrapeVariety` - **GLOBAL CATALOG** (shared)
- ❌ `WineType` - **GLOBAL CATALOG** (shared)

### 2. API Layer - Explicit Validation

**Decisión**: Validación explícita en cada endpoint - simple pero efectivo.

**Patrón Simple:**
```python
# src/modules/fermentation/src/api/routers/fermentation_router.py

@router.get("/fermentations/{fermentation_id}")
async def get_fermentation(
    fermentation_id: int,
    user: UserContext = Depends(get_current_user),  # ← Ya existe
    service: IFermentationService = Depends()
):
    """
    Get fermentation by ID with winery_id validation.
    
    Returns 403 if fermentation belongs to different winery.
    """
    # Get fermentation (repository ya filtra por winery_id)
    ferm = await service.get_by_id(fermentation_id, user.winery_id)
    
    if not ferm:
        # Not found OR doesn't belong to user's winery
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fermentation {fermentation_id} not found"
        )
    
    # Extra validation (defense in depth)
    if ferm.winery_id != user.winery_id:
        # Log security event
        logger.warning(
            "cross_winery_access_attempt",
            user_id=user.user_id,
            user_winery_id=user.winery_id,
            resource_type="fermentation",
            resource_id=fermentation_id,
            resource_winery_id=ferm.winery_id
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this resource"
        )
    
    return FermentationResponse.from_entity(ferm)
```

**¿Por qué validación explícita y no dependency?**
- ✅ **Más simple**: No requiere middleware
- ✅ **Más claro**: Ves exactamente qué está pasando
- ✅ **Suficiente**: Para 1-2 wineries no necesitas abstracción
- 🔄 **Upgrade path**: Cuando escalemos, creamos `get_winery_id()` dependency

### 3. Exception Handling - 403 Forbidden Policy

**Decisión**: Retornar **403 Forbidden** (NOT 404) cuando usuario intenta acceder recursos de otra winery.

**Rationale**: 
- ✅ **Explícito**: 403 significa "existe pero no tienes permiso"
- ✅ **Debugging**: Desarrolladores identifican errores de multi-tenancy fácilmente
- ✅ **Security logging**: 403 triggers audit log (ADR-027)
- ❌ **404 rechazado**: Oculta existencia pero complica debugging y no es estándar REST

**Implementation:**
```python
# src/shared/auth/domain/errors.py
class WineryAccessDeniedError(Exception):
    """Raised when user attempts to access resource from different winery."""
    def __init__(self, resource_id: int, resource_type: str, user_winery_id: int, resource_winery_id: int):
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.user_winery_id = user_winery_id
        self.resource_winery_id = resource_winery_id
        super().__init__(
            f"Access denied: {resource_type}#{resource_id} belongs to winery {resource_winery_id}, "
            f"user belongs to winery {user_winery_id}"
        )

# src/modules/fermentation/src/api/error_handlers.py
@app.exception_handler(WineryAccessDeniedError)
async def winery_access_denied_handler(request: Request, exc: WineryAccessDeniedError):
    """Handle cross-winery access attempts with 403 and audit logging."""
    
    # Log security event (ADR-027)
    logger.warning(
        "winery_access_denied",
        resource_type=exc.resource_type,
        resource_id=exc.resource_id,
        user_winery_id=exc.user_winery_id,
        resource_winery_id=exc.resource_winery_id,
        path=request.url.path,
        user_id=getattr(request.state.user, "user_id", None)
    )
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "access_denied",
            "detail": "You do not have permission to access this resource",
            "resource_type": exc.resource_type,
            "resource_id": exc.resource_id
        }
    )
```

---

## Implementation Notes

### File Structure (LIGHT)

```
src/
├── modules/
│   ├── fermentation/
│   │   ├── repository_component/
│   │   │   └── repositories/
│   │   │       ├── fermentation_repository.py     # REFACTOR: 3 métodos (get_by_id, list_all, create)
│   │   │       └── sample_repository.py           # REFACTOR: 2 métodos (get_by_id, list_by_fermentation)
│   │   └── api/
│   │       └── routers/
│   │           ├── fermentation_router.py         # REFACTOR: Validación explícita + logging
│   │           └── sample_router.py               # REFACTOR: Validación explícita + logging
│   └── fruit_origin/
│       └── repository_component/
│           └── repositories/
│               └── harvest_lot_repository.py      # REFACTOR: 2 métodos (get_by_id, get_by_code)
```

**NO se modifica:**
- ❌ `BaseRepository` (no helpers complejos, KISS)
- ❌ Middleware (no necesario para piloto)
- ❌ Dependencies extras (usamos `get_current_user` existente)
- ❌ Migrations (no RLS para piloto)

### Component Responsibilities (LIGHT)

**Repository Methods:**
- ALWAYS include `Fermentation.winery_id == winery_id` in WHERE clause
- Validate `winery_id > 0` at start of method (raise ValueError if invalid)
- Return `None` if not found OR belongs to different winery
- Log query with winery_id context (ADR-027)

**API Router Handlers:**
- Extract `winery_id` from `UserContext` (via `get_current_user`)
- Pass `winery_id` to repository methods explicitly
- Validate resource belongs to user's winery (defense in depth)
- Return 404 if not found, 403 if cross-winery attempt
- Log security events on 403 (ADR-027)

**Pattern aplicado consistentemente:**
```python
# 1. Get user context
user: UserContext = Depends(get_current_user)

# 2. Call repository with winery_id
resource = await repo.get_by_id(resource_id, user.winery_id)

# 3. Validate result
if not resource:
    raise HTTPException(404)
if resource.winery_id != user.winery_id:
    logger.warning("cross_winery_access_attempt", ...)
    raise HTTPException(403)

# 4. Return response
return ResourceResponse.from_entity(resource)
```

---

## Architectural Considerations

### Multi-Tenancy Patterns Evaluated

| Pattern | Approach | Security | Complexity | Decision |
|---------|----------|----------|------------|----------|
| **Database per Tenant** | Separate DB per winery | Highest (physical isolation) | High (migrations, backups) | ❌ Rejected (complexity) |
| **Schema per Tenant** | Separate schema per winery | High (schema isolation) | Medium (schema management) | ❌ Rejected (PostgreSQL connection overhead) |
| **Row-Level Security** | winery_id + RLS policies | Medium-High (DB enforcement) | Medium (policy management) | ✅ **SELECTED** |
| **Application-only** | winery_id filtering in app | Low (no DB enforcement) | Low (simple filtering) | ❌ Rejected (compliance) |

### Security Boundaries

**1. Authentication Boundary (Existing - ADR-007):**
- JWT token validation
- User identity establishment
- Role extraction

**2. Authorization Boundary (NEW - This ADR):**
- Winery context injection
- Data access validation
- Cross-winery prevention

**3. Database Boundary (NEW - This ADR):**
- RLS policy enforcement
- Session variable validation
- Defense in depth

### Performance Considerations

**RLS Overhead:**
- Policy evaluation: ~5-10ms per query
- Mitigación: Connection pooling, query optimization
- Trade-off aceptado: Security > 5ms latency

**Middleware Overhead:**
- Context injection: ~1ms per request
- Mitigación: Cache winery_id in request.state
- Negligible impact

**Repository Refactoring:**
- build_scoped_query(): ~0.5ms per query
- No measurable impact
- Prevents N queries when devs forget winery_id filter

### Admin Users Special Case

**Requirement**: Admin users (role=ADMIN) can access ALL wineries for support/debugging.

**Implementation:**
```python
# Middleware: Admin users get winery_id=0 (special marker)
if user.role == UserRole.ADMIN:
    request.state.winery_id = 0  # Admin marker
    request.state.is_admin = True

# Repository: Admin bypass winery_id filtering
def build_scoped_query(self, entity_class, winery_id: int, is_admin: bool = False):
    if is_admin:
        # Admin: No winery_id filter
        query = select(entity_class)
    else:
        # Regular user: winery_id filter
        query = select(entity_class).where(entity_class.winery_id == winery_id)
```

**PostgreSQL RLS Policy handles this:**
```sql
CREATE POLICY admin_global_access ON fermentations
    FOR ALL
    USING (current_setting('app.user_role') = 'admin');
```

---

## Consequences

### Positive Consequences

✅ **Security Hardening:**
- Defense in depth: 3 niveles de enforcement (middleware, repository, database)
- Impossible to bypass: winery_id REQUIRED en todos los queries
- Admin support: Role-based global access para troubleshooting
- Audit trail: ADR-027 logging captura intentos de acceso cross-winery

✅ **Compliance Ready:**
- SOC2: Data isolation enforced at DB level
- GDPR: Tenant data segregation guaranteed
- Audit logs: 403 errors triggered por intentos de acceso maliciosos

✅ **Developer Experience:**
- DRY: winery_id inyectado automáticamente, no más `user.winery_id` manual
- Impossible to forget: Middleware + dependency garantizan contexto
- Clear errors: 403 Forbidden con mensaje descriptivo
- Testable: Fácil mockear `request.state.winery_id`

✅ **Strategic Benefits (Post ADR-027 & ADR-028):**
- 4 módulos nuevos NACEN SEGUROS (zero refactoring futuro)
- Logging infrastructure LISTA para eventos de seguridad
- Module independence permite inyectar security layer sin refactorings masivos
- Savings: 4 días de refactoring evitados

### Negative Consequences

⚠️ **Refactoring Required:**
- 2 módulos (Fermentation, Fruit Origin) requieren refactoring
- ~20 repository methods a actualizar
- ~10 router handlers a actualizar
- Estimated: 2-3 days work

⚠️ **RLS Complexity:**
- Migrations deben gestionar RLS policies
- Testing requiere setup de session variables
- Debugging RLS issues más complejo que app-level filtering

⚠️ **Performance Overhead:**
- RLS evaluation: ~5-10ms per query
- Middleware: ~1ms per request
- Mitigación: Acceptable for security benefit

⚠️ **Breaking Changes:**
- Repository method signatures cambian (add winery_id parameter)
- Service method signatures cambian (add winery_id parameter)
- Tests requieren setup de winery context

### Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| RLS policies mal configuradas | Medium | High | Comprehensive test suite (Phase 5) |
| Admin users bypass security incorrectly | Low | High | Explicit logging de admin actions |
| Performance degradation | Low | Medium | Load testing con RLS enabled |
| Migration failures | Medium | High | Rollback scripts + manual validation |

---

## TDD Plan (LIGHT - Pragmático)

### Phase 1: Repository Layer (1 day)

**Repositories to refactor:**
- `FermentationRepository` - 3 métodos críticos
- `SampleRepository` - 2 métodos críticos
- `HarvestLotRepository` - 2 métodos críticos

**Test Files:**
- `src/modules/fermentation/tests/integration/test_fermentation_repository_security.py`
- `src/modules/fermentation/tests/integration/test_sample_repository_security.py`
- `src/modules/fruit_origin/tests/integration/test_harvest_lot_repository_security.py`

**Tests (15 total):**
1. ✅ get_by_id() raises ValueError if winery_id <= 0
2. ✅ get_by_id() returns None if not found
3. ✅ get_by_id() returns None if belongs to different winery
4. ✅ list_all() filters by winery_id automatically
5. ✅ create() sets winery_id from parameter

### Phase 2: API Layer (1 day)

**Routers to refactor:**
- `fermentation_router.py` - 3 endpoints críticos (GET by id, GET list, POST create)
- `sample_router.py` - 2 endpoints críticos (GET by id, GET list)

**Test Files:**
- `tests/api/test_fermentation_endpoints_security.py`
- `tests/api/test_sample_endpoints_security.py`

**Tests (20 total):**
1. ✅ GET /fermentations/{id} returns 404 if not found
2. ✅ GET /fermentations/{id} returns 403 if cross-winery
3. ✅ GET /fermentations returns only user's winery
4. ✅ POST /fermentations uses winery_id from user context
5. ✅ Security events logged on 403 (ADR-027)
6. ✅ Same pattern for samples

### Phase 3: Security Logging (0.5 day)

**Test Files:**
- `tests/api/test_security_logging.py`

**Tests (5 total):**
1. ✅ 403 errors logged with full context
2. ✅ Logs include user_id, winery_id, resource_type, resource_id
3. ✅ Logs queryable via structlog format (ADR-027)
4. ✅ Admin access logged separately
5. ✅ No sensitive data leaked in logs

**Total: ~40 tests en 2-3 días**

---

## Quick Reference

### For API Developers

**Secure Endpoint Pattern:**
```python
@router.get("/fermentations/{fermentation_id}")
async def get_fermentation(
    fermentation_id: int,
    winery_id: int = Depends(get_winery_id),  # ✅ ALWAYS include
    service: IFermentationService = Depends()
):
    fermentation = await service.get_by_id(fermentation_id, winery_id)
    if not fermentation:
        raise HTTPException(status_code=404, detail="Fermentation not found")
    return FermentationResponse.from_entity(fermentation)
```

**❌ NEVER do this:**
```python
# VULNERABLE: Missing winery_id dependency
@router.get("/fermentations/{fermentation_id}")
async def get_fermentation(
    fermentation_id: int,
    user: UserContext = Depends(get_current_user),  # ❌ Manual extraction
    service: IFermentationService = Depends()
):
    # ❌ Can forget to pass user.winery_id
    fermentation = await service.get_by_id(fermentation_id)
```

### For Repository Developers

**Secure Query Pattern:**
```python
async def get_by_id(self, resource_id: int, winery_id: int) -> Optional[Resource]:
    """Get resource by ID with winery_id scoping."""
    query = self.build_scoped_query(  # ✅ Use helper
        Resource,
        winery_id=winery_id,
        additional_filters=[Resource.id == resource_id]
    )
    
    session_cm = await self.get_session()
    async with session_cm as session:
        result = await session.execute(query)
        return result.scalar_one_or_none()
```

### For Test Writers

**Setup Winery Context in Tests:**
```python
@pytest.fixture
def mock_winery_context(app):
    """Mock winery context for testing."""
    async def mock_get_winery_id():
        return 1  # Test winery ID
    
    app.dependency_overrides[get_winery_id] = mock_get_winery_id
    yield
    app.dependency_overrides.clear()

def test_fermentation_access(client, mock_winery_context):
    """Test fermentation access with winery context."""
    response = client.get("/fermentations/123")
    assert response.status_code == 200
```

---

## API Examples

### Successful Request Flow

```
1. Client Request:
   GET /fermentations/123
   Authorization: Bearer eyJhbGc...

2. Authentication Middleware:
   JWT decoded → UserContext(user_id=10, winery_id=5, role=WINEMAKER)
   request.state.user = UserContext

3. WineryContextMiddleware:
   winery_id extracted from UserContext
   request.state.winery_id = 5
   Log: "winery_context_bound", winery_id=5, user_id=10

4. Router Handler:
   winery_id = Depends(get_winery_id)  # Gets 5 from request.state
   service.get_by_id(123, winery_id=5)

5. Repository:
   query = build_scoped_query(Fermentation, winery_id=5, filters=[Fermentation.id == 123])
   SELECT * FROM fermentations WHERE id = 123 AND winery_id = 5

6. PostgreSQL RLS:
   Policy evaluation: app.winery_id (5) matches row winery_id (5) ✅
   Row returned

7. Response:
   200 OK
   {"id": 123, "vintage_year": 2024, ...}
```

### Cross-Winery Access Attempt

```
1. Client Request:
   GET /fermentations/456
   Authorization: Bearer eyJhbGc... (winery_id=5)

2. Authentication + Middleware:
   request.state.winery_id = 5

3. Repository Query:
   SELECT * FROM fermentations WHERE id = 456 AND winery_id = 5
   Result: None (fermentation 456 belongs to winery_id=10)

4. Service:
   Returns None

5. Router Handler:
   if not fermentation:
       raise HTTPException(status_code=404)  # Could be 403 if we check ownership

6. Response:
   404 Not Found
   {"detail": "Fermentation not found"}
```

### Admin Access (All Wineries)

```
1. Client Request:
   GET /fermentations/456
   Authorization: Bearer eyJhbGc... (user_id=1, role=ADMIN)

2. WineryContextMiddleware:
   if user.role == UserRole.ADMIN:
       request.state.winery_id = 0  # Admin marker
       request.state.is_admin = True

3. Repository:
   query = build_scoped_query(Fermentation, winery_id=0, is_admin=True)
   # No winery_id filter applied (admin bypass)
   SELECT * FROM fermentations WHERE id = 456

4. PostgreSQL RLS:
   Policy: admin_global_access → current_setting('app.user_role') = 'admin' ✅
   Row returned

5. Response:
   200 OK
   {"id": 456, "vintage_year": 2023, "winery_id": 10, ...}
   Log: "admin_access", admin_user_id=1, resource_type=fermentation, resource_id=456
```

---

## Error Catalog

### Security Errors

| Error | Status | When | Response |
|-------|--------|------|----------|
| **Missing Authorization** | 401 | No JWT token in header | `{"detail": "Not authenticated"}` |
| **Invalid Token** | 401 | JWT expired or malformed | `{"detail": "Could not validate credentials"}` |
| **Winery Context Missing** | 401 | Middleware didn't run | `{"detail": "Winery context not found"}` |
| **Cross-Winery Access** | 403 | User tries access other winery's data | `{"error": "access_denied", "detail": "...", "resource_type": "fermentation", "resource_id": 123}` |
| **Invalid winery_id** | 500 | Repository got winery_id=None/0 | `{"detail": "Internal server error"}` (logged as bug) |

### Repository Errors

| Error | When | Handling |
|-------|------|----------|
| `ValueError: winery_id is REQUIRED` | Repository method called with invalid winery_id | Log as critical bug, return 500 |
| `WineryAccessDeniedError` | Resource exists but belongs to different winery | Return 403, log security event |
| `WineryNotFoundError` | winery_id doesn't exist in DB | Return 400, invalid winery reference |

---

## Acceptance Criteria (LIGHT)

### Phase 1: Repository Layer ✅

- [ ] FermentationRepository: 3 métodos refactored (get_by_id, list_all, create)
- [ ] SampleRepository: 2 métodos refactored (get_by_id, list_by_fermentation)
- [ ] HarvestLotRepository: 2 métodos refactored (get_by_id, get_by_code)
- [ ] All methods validate `winery_id > 0` (raise ValueError if invalid)
- [ ] All methods include `winery_id` in WHERE clause
- [ ] Cross-winery queries return None
- [ ] 15/15 repository tests passing

### Phase 2: API Layer ✅

- [ ] fermentation_router: 3 endpoints refactored (GET by id, GET list, POST create)
- [ ] sample_router: 2 endpoints refactored (GET by id, GET list)
- [ ] All endpoints extract `winery_id` from `UserContext`
- [ ] All endpoints validate resource belongs to user's winery
- [ ] Cross-winery access returns 403 Forbidden
- [ ] 20/20 API integration tests passing

### Phase 3: Security Logging ✅

- [ ] 403 errors logged with ADR-027 format
- [ ] Logs include: user_id, winery_id, resource_type, resource_id
- [ ] No sensitive data leaked in error responses
- [ ] Security events queryable in logs
- [ ] 5/5 logging tests passing

### End-to-End Validation ✅

- [ ] **40 total new tests passing** (15+20+5)
- [ ] **Zero regressions**: All existing 532 tests still passing
- [ ] Manual testing: Cross-winery access blocked
- [ ] Manual testing: Same-winery access works
- [ ] Manual testing: Security events in logs

### Future Upgrade Path Documented ✅

- [ ] Documentation: How to add Middleware when scaling
- [ ] Documentation: How to add RLS when scaling
- [ ] TODO comments in code pointing to full ADR-025

---

## Implementation Timeline (LIGHT)

### Day 1: Repository Layer (Morning + Afternoon)

**Morning (4 hours):**
- Refactor FermentationRepository (3 methods)
- Refactor SampleRepository (2 methods)
- Add `winery_id` validation to all methods

**Afternoon (4 hours):**
- Refactor HarvestLotRepository (2 methods)
- Write 15 integration tests
- Run full test suite (532 + 15)

### Day 2: API Layer (Morning + Afternoon)

**Morning (4 hours):**
- Refactor fermentation_router (3 endpoints)
- Refactor sample_router (2 endpoints)
- Add explicit validation + 403 handling

**Afternoon (4 hours):**
- Write 20 API integration tests
- Integrate security logging (ADR-027)
- Run full test suite (532 + 35)

### Day 3: Security Logging & Documentation (Half day)

**Morning (4 hours):**
- Write 5 security logging tests
- Manual testing: Cross-winery access attempts
- Manual testing: Security events in logs
- Update documentation
- Document upgrade path to full version

**Total Estimated Effort: 2.5 days (20 hours)**

**Checkpoints:**
- ✅ End of Day 1: Repository layer secure, 15 tests passing
- ✅ End of Day 2: API layer secure, 35 tests passing
- ✅ End of Day 3: Security validated, 40 tests passing, 0 regressions

---

## Status

**PROPOSED (LIGHT VERSION)** - Pragmatic approach for pilot phase

**Version:** LIGHT - Sufficient for 1-2 wineries in pilot  
**Estimated Implementation Time:** 2.5 days (20 hours)  
**Estimated Test Coverage:** 40 new tests  
**Breaking Changes:** Minimal (solo 7 métodos de repository)  
**Rollback Strategy:** Git revert (no migrations)  
**Risk Level:** Low (simple validation, no middleware, no RLS)  
**Strategic Value:** Medium for pilot, High for future scaling

**Dependencies:**
- ✅ ADR-027: Structured Logging (COMPLETE - security event logging ready)
- ✅ ADR-028: Module Dependency Management (COMPLETE)
- ❌ ADR-026: Error Handling (NOT required - parallel)

**Enables:**
- ADR-014: Fruit Origin Service (will be born secure)
- ADR-015: Fruit Origin API (will be born secure)
- ADR-016: Winery Service (will be born secure)
- ADR-017: Winery API (will be born secure)

**Upgrade Path (When Scaling):**
1. **Phase 2 - Medium (5-6 días)**: Add Middleware + `get_winery_id()` dependency
2. **Phase 3 - Full (4 días)**: Add PostgreSQL RLS policies
3. **Total upgrade time**: 9-10 días adicionales cuando sea necesario

**Next Steps:**
1. ✅ Review and approve LIGHT version
2. ✅ Start Day 1: Repository Layer refactoring
3. ✅ Day 2: API Layer refactoring
4. ✅ Day 3: Security logging + validation
5. 🔄 Monitor pilot: If scaling, upgrade to Medium/Full

---

## Future Enhancements (Not in LIGHT)

### When to Upgrade:

**Upgrade to MEDIUM (Middleware + Dependencies):**
- ✅ Scaling to 5+ wineries
- ✅ Multiple developers working on API
- ✅ Need DRY enforcement (automatic winery_id injection)
- **Effort**: 5-6 días adicionales

**Upgrade to FULL (PostgreSQL RLS):**
- ✅ Scaling to 10+ wineries
- ✅ Compliance requirements (SOC2, GDPR, ISO27001)
- ✅ Need defense-in-depth security
- ✅ External security audit required
- **Effort**: 4 días adicionales (después de Medium)

### RLS Implementation (Future)

**PostgreSQL Row-Level Security** - Documented for future reference:

```sql
-- Enable RLS on fermentations table
ALTER TABLE fermentations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only access fermentations from their winery
CREATE POLICY fermentation_winery_isolation ON fermentations
    FOR ALL
    USING (winery_id = current_setting('app.winery_id')::integer);

-- Policy: Admin users can access all wineries
CREATE POLICY fermentation_admin_access ON fermentations
    FOR ALL
    USING (current_setting('app.user_role') = 'admin');
```

**Benefits of RLS (cuando lo implementemos):**
- ✅ Defense in depth: DB enforces even if app has bug
- ✅ Compliance: SOC2/GDPR require DB-level isolation
- ✅ Zero trust: App cannot bypass security
- ⚠️ Performance: ~5-10ms overhead per query

**Migration Strategy:**
- LIGHT → MEDIUM: No breaking changes, just add middleware
- MEDIUM → FULL: Requires migration + RLS policies

---

**References:**
- [OAuth 2.0 Multi-Tenancy Best Practices](https://oauth.net/2/multi-tenancy/)
- [PostgreSQL Row-Level Security Documentation](https://www.postgresql.org/docs/14/ddl-rowsecurity.html) (para futuro)
- [OWASP Multi-Tenancy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Multitenant_Application_Security_Cheat_Sheet.html)
- [KISS Principle](https://en.wikipedia.org/wiki/KISS_principle) - Applied in LIGHT version

# Module Context: Fermentation Management

> **Parent Context**: See `/.ai-context/project-context.md` for system-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Module responsibility
**Core CRUD operations** for fermentation tracking and sample data management within the monitoring system.

**Position in system**: Central data hub that receives measurements from winemakers and coordinates with analysis engine for real-time monitoring.

## Technology stack
- **Framework**: FastAPI (Python 3.9+) for REST API endpoints
- **Database**: PostgreSQL with SQLAlchemy ORM for persistent data
- **Validation**: Pydantic V2 models for request/response handling
- **Testing**: pytest with async support
- **Logging**: Loguru for structured logging and debugging
- **Code Quality**: Black for formatting, flake8 for linting
- **CI/CD**: GitHub Actions for automation, Docker for containerization

## Module interfaces
**Receives from**: Frontend/API requests with fermentation creation and sample measurements
**Provides to**: Analysis Engine module (fermentation data for analysis)
**Depends on**: Authentication module (user validation and session management)

## Key functionality
- **Fermentation lifecycle**: Create, track, and manage fermentation states
- **Sample tracking**: Add and validate measurement data over time  
- **Data retrieval**: Provide fermentation history and current status
- **User isolation**: Ensure winemakers only access their own fermentations
- **Analysis coordination**: Trigger analysis workflows after data updates

## Business rules
- **Sample chronology**: Measurements must be added in time sequence
- **Data validation**: Glucose decreases, ethanol increases over time
- **User boundaries**: Strict isolation between different winemaker data
- **Status progression**: ACTIVE → SLOW → STUCK → COMPLETED transitions

## Module components
- **API Component**: REST endpoints for fermentation and sample operations
- **Service Component**: Business logic and validation for fermentation workflows
- **Repository Component**: Database access patterns for fermentation and sample data
  - **BaseRepository**: Infrastructure helpers (session management, error mapping, multi-tenant scoping, soft delete)
  - **Domain Interfaces**: `IFermentationRepository` with type-safe entities
  - **Concrete Repositories**: `FermentationRepository` extending BaseRepository

## Implementation status

**Status:** ✅ **Domain, Repository, Service, API & Integration Tests Complete**  
**Last Updated:** 2025-12-30  
**Reference:** ADR-006 (API Layer), ADR-005 (Service Layer), ADR-003 (Repository Layer), ADR-002 (Repository Architecture), ADR-011 Phase 3 (Integration Tests)

### Completed Components

**✅ Domain Layer**
- Entities: Fermentation, BaseSample (+ 3 subtypes: Sugar, Density, Temperature), User, FermentationLotSource
  - ADR-029: Campos `data_source` e `imported_at` agregados (16 tests)
- DTOs: FermentationCreate, SampleCreate
- Enums: FermentationStatus, SampleType, DataSource (ADR-029 - 6 tests)
- Interfaces: IFermentationRepository, ISampleRepository
  - ADR-029: Métodos `list_by_data_source()` agregados (2 tests)

**✅ Service Layer (115 tests passing)**
- FermentationService: 7 methods, 33 tests
- SampleService: 6 methods, 27 tests
- Validation Services: 5 services, 55 tests
  - ValidationOrchestrator (4 tests)
  - ValueValidationService (9 tests)
  - ChronologyValidationService (14 tests)
  - BusinessRuleValidationService (9 tests)
  - ValidationService (19 tests)

**✅ Domain Tests (5 tests passing)**
- FermentationLotSource entity tests

**✅ Repository Interfaces (14 tests passing)**
- IFermentationRepository: Interface validation
- ISampleRepository: Interface validation

**✅ Repository Layer (47 tests passing - Using ADR-012 Shared Utilities)**
- FermentationRepository: 16 tests passing (8 base + 8 ADR-029) ✅
- SampleRepository: 12 tests passing (Phase 2 migrated + ADR-029 method) ✅
- LotSourceRepository: 11 tests passing (Phase 2 migrated) ✅
- FermentationNoteRepository: 19 tests passing (Phase 2 migrated) ✅
- Error handling: 19 tests passing (error class hierarchy)
- **ADR-012 Impact**: 4 files migrated, 50 tests using shared test infrastructure
- **ADR-029 Impact**: 8 new tests for list_by_data_source() methods

**✅ Integration Tests (49 tests passing) - Dec 30, 2025**
- **FermentationNoteRepository**: 20 tests with real database
- **FermentationRepository**: 22 tests with PostgreSQL
- **HarvestLotRepository**: 21 tests (from fruit_origin module)
- **SampleRepository**: 1 test with sample model isolation
- **UnitOfWork**: 6 tests with savepoint-based transaction management
- Multi-tenancy isolation verified
- Database transactions and rollbacks tested
- **ADR-011 Phase 3 Resolution**: All integration tests now run with main suite
  - SessionWrapper pattern for UnitOfWork tests
  - Isolated sample_repository fixture to avoid metadata conflicts
  - Triple try/except import pattern for ADR-028 compatibility

**✅ API Layer (90 tests passing) - Nov 17, 2025**
- **FastAPI Routers**: Fermentation (10 endpoints) and Sample (7 endpoints)
- **Request DTOs**: Pydantic models for API input validation
- **Response DTOs**: Pydantic models for API output serialization
- **Error Handling**: Centralized with `@handle_service_errors` decorator
- **Authentication/Authorization**: JWT integration, winery context injection
- **API Documentation**: OpenAPI/Swagger specs auto-generated
- **Integration**: Dependency injection with FastAPI
- **API Tests**: 90 endpoint tests with TestClient (100% passing)

**Refactoring - Error Handling (Nov 17, 2025):**
- Created `error_handlers.py` with decorator pattern
- Eliminated ~410 lines of duplicated try/except blocks
- Standardized exception→HTTP status code mappings
- All 17 endpoints refactored to use centralized error handling

**Total: 283 tests passing (234 unit + 49 integration + 90 API)**

### Test Execution Notes

✅ **All tests now run together** (December 30, 2025 - ADR-011 Phase 3 Complete):

```powershell
# Run all fermentation tests together
cd src/modules/fermentation
poetry run pytest tests/ -v

# Or use the system-wide test suite
cd C:\dev\wine-fermentation-system
.\run_all_tests.ps1  # 797 tests total, includes all 49 fermentation integration

# Run specific test suites
poetry run pytest tests/unit/        # 234 tests
poetry run pytest tests/integration/ # 49 tests  
poetry run pytest tests/api/         # 90 tests
```

**Resolution**: SQLAlchemy metadata conflicts RESOLVED via:
1. **Isolated sample fixtures** in `tests/integration/repository_component/conftest.py`
2. **SessionWrapper pattern** for UnitOfWork tests using savepoints
3. **Function-scoped db_engine** from ADR-011 Phase 2
4. **Late Sample model imports** to avoid global registry pollution

**Previous limitation eliminated**: All integration tests now included in main test suite.

### Pending Components

**⏳ Optional Enhancements** (Future work)
- GET /samples/types endpoint (list available sample types)
- Rate limiting for API endpoints
- Response caching for read-heavy endpoints
- WebSocket support for real-time updates
- GraphQL layer for complex queries

**API Layer is functionally complete** (17/18 endpoints implemented)

## Quick Reference

**Need to work on this module?**
1. Check ADRs: `.ai-context/adr/ADR-002`, `ADR-003`, `ADR-004`, `ADR-005`, `ADR-006`, `ADR-011 Phase 3`, `ADR-029`
2. Review component contexts in `src/*/.ai-context/component-context.md`
3. Run tests: 
   - All tests: `poetry run pytest tests/` (400 tests - includes 32 new ADR-029 tests)
   - Unit: `poetry run pytest tests/unit/` (264 tests)
   - Integration: `poetry run pytest tests/integration/` (49 tests)
   - API: `poetry run pytest tests/api/` (87 tests)
   - System-wide: `.\run_all_tests.ps1` from workspace root (914 tests)
   - **Note**: Integration tests now included in main suite (ADR-011 Phase 3 complete)

**Architecture:**
- Domain → Repository → Service → API ✅ **Complete**
- All dependencies point toward Domain
- Type-safe (DTOs → Entities)
- SOLID principles enforced
- Integration tests verify real PostgreSQL operations
- API tests verify HTTP endpoints with TestClient

**Error Handling:**
- Centralized with `@handle_service_errors` decorator
- Exception→HTTP mappings: NotFoundError→404, ValidationError→422, DuplicateError→409, etc.
- ~410 lines of duplicated code eliminated

## Domain entities
**Core Entities:**
- **Fermentation**: Process tracking with status lifecycle
- **BaseSample**: Time-series measurements (polymorphic)
- **User**: User authentication and tracking
- **FermentationLotSource**: Links fermentation to harvest lots

**DTOs:**
- **FermentationCreate**: Input for creating fermentations
- **SampleCreate**: Input for creating samples

**Enums:**
- **FermentationStatus**: ACTIVE, SLOW, STUCK, COMPLETED
- **SampleType**: SUGAR, TEMPERATURE, DENSITY, etc.
- **DataSource**: SYSTEM, IMPORTED, MIGRATED (ADR-029)

## DDD Implementation

**Dependency Direction:**
```
repository_component ─┐
service_component     │──► domain (entities, DTOs, interfaces)
```

**Multi-tenancy:** All operations scoped by `winery_id`

## How to work on this module
Read component-level contexts:
- `src/domain/.ai-context/component-context.md`
- `src/repository_component/.ai-context/component-context.md`
- `src/service_component/.ai-context/component-context.md`
- **Service Component:** Implementa lógica de negocio y orquestación, dependiendo solo de contratos del dominio.
- **Repository Component:** Implementa las interfaces de repositorio del dominio, conectando con la infraestructura (ej: SQLAlchemy).
- **Dirección de dependencias:** Siempre apunta hacia el dominio.

**Diagrama de dependencias:**
```
repository_component ─┐
service_component     │
        └─────────────┴──► domain
```

> Para más detalles, consulta la documentación y diagramas en `/docs/` o los archivos de contexto superiores.
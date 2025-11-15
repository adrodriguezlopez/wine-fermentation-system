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

**Status:** ✅ **Domain, Repository, Service & API Complete**  
**Last Updated:** 2025-11-17  
**Reference:** ADR-006 (API Layer), ADR-005 (Service Layer), ADR-003 (Repository Layer), ADR-002 (Repository Architecture)

### Completed Components

**✅ Domain Layer**
- Entities: Fermentation, BaseSample (+ 3 subtypes: Sugar, Density, Temperature), User, FermentationLotSource
- DTOs: FermentationCreate, SampleCreate
- Enums: FermentationStatus, SampleType
- Interfaces: IFermentationRepository, ISampleRepository

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

**✅ Repository Layer (39 tests passing)**
- FermentationRepository: 8 tests passing (5 methods implemented)
- SampleRepository: 12 tests passing (11 methods implemented)
- Error handling: 19 tests passing (error class hierarchy)

**✅ Integration Tests (9 tests passing)**
- FermentationRepository integration: 8 tests with real PostgreSQL
- SampleRepository integration: 1 test with real PostgreSQL
- Multi-tenancy isolation verified
- Database transactions and rollbacks tested

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

**Total: 272 tests passing (173 unit + 9 integration + 90 API)**

### Test Execution Notes

⚠️ **Important**: Due to SQLAlchemy mapper registry conflicts, unit and integration tests must be run separately:

```powershell
# Run unit tests (173 tests)
poetry run pytest tests/unit/

# Run integration tests (9 tests) 
poetry run pytest tests/integration/

# Run API tests (90 tests)
poetry run pytest tests/api/

# Run all tests sequentially
poetry run pytest tests/unit/ --tb=no -q; poetry run pytest tests/integration/ --tb=no -q; poetry run pytest tests/api/ --tb=no -q
```

**Why separate?** The global SQLAlchemy mapper registry gets configured during pytest collection. When both test suites are collected together, entity re-imports cause mapper conflicts with polymorphic inheritance (`SugarSample` inheriting from `BaseSample`). Running separately avoids this issue.

**See**: `tests/README.md` for detailed explanation.

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
1. Check ADRs: `.ai-context/adr/ADR-002`, `ADR-003`, `ADR-004`, `ADR-005`, `ADR-006`
2. Review component contexts in `src/*/.ai-context/component-context.md`
3. Run tests: 
   - Unit: `poetry run pytest tests/unit/` (173 tests)
   - Integration: `poetry run pytest tests/integration/` (9 tests)
   - API: `poetry run pytest tests/api/` (90 tests)
   - **Note**: Must run separately due to SQLAlchemy mapper conflicts (see tests/README.md)

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
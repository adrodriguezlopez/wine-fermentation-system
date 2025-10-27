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

**Status:** ✅ **COMPLETE - All Layers Implemented & Tested**  
**Last Updated:** 2025-10-26  
**Reference:** ADR-005 (Service Layer), ADR-003 (Repository Layer), ADR-002 (Repository Architecture)

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
- **Previous Issue RESOLVED**: SQLAlchemy mapper error fixed by removing duplicate imports

**Total: 173 unit tests passing (100% success rate)**

### Pending Components

**🔄 API Layer** (Next phase)
- FastAPI endpoints for services
- Request/response DTOs
- HTTP error mapping
- Authentication integration

## Quick Reference

**Need to work on this module?**
1. Check ADRs: `.ai-context/adr/ADR-002`, `ADR-003`, `ADR-004`, `ADR-005`
2. Review component contexts in `src/*/. ai-context/component-context.md`
3. Run tests: `poetry run pytest src/modules/fermentation/tests/`

**Architecture:**
- Domain → Repository → Service → API (future)
- All dependencies point toward Domain
- Type-safe (DTOs → Entities)
- SOLID principles enforced

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
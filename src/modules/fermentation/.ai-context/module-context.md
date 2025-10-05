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

**Status:** ✅ **Repository Layer Complete** - Service layer integration pending  
**Last Updated:** 2025-10-04  
**Reference:** ADR-003 Phase 2 completion

### Completed Components

**✅ Repository Infrastructure (ADR-002 & ADR-003)**
- **BaseRepository:** Common repository functionality (session management, error mapping, multi-tenant scoping)
- **Error Infrastructure:** Complete error hierarchy with PostgreSQL SQLSTATE mapping
- **Database Infrastructure:** Connection management, session handling, lazy loading
- **Domain Interfaces:** Type-safe repository contracts (IFermentationRepository, ISampleRepository)

**✅ FermentationRepository (ADR-003 Phase 2)**
- **Methods:** 5 (fermentation lifecycle only - samples removed per ADR-003)
- **Tests:** 8 passing (100% interface coverage)
- **Status:** Fully implemented with SQLAlchemy integration
- **Separation:** Zero sample operations (moved to SampleRepository)

**✅ SampleRepository (ADR-003 Phase 2)**
- **Methods:** 11 (1 implemented: `create()`, 10 stubs)
- **Tests:** 12 passing (interface validation via TDD pragmatic approach)
- **Status:** Structure complete, implementation 9% complete
- **Architecture:** All sample operations centralized (no mixing with fermentation)

### Test Metrics
- **Total:** 102 tests passing (95 → 102, +7.4% growth)
- **Repository tests:** 20 (8 fermentation + 12 sample)
- **Other components:** 82 tests
- **Integration tests:** 0 (pending Phase 3)
- **Coverage:** Interface contracts 100% validated

### Next Steps (Phase 3)
1. **Integration tests** for SampleRepository methods
2. **Implement remaining 10 SampleRepository methods** (TDD cycle)
3. **Update FermentationService** to inject SampleRepository
4. **Service layer migration** (sample operations → SampleRepository)

## Domain entities
**Core Entities:**
- **Fermentation**: Process tracking with status lifecycle (ACTIVE → SLOW → STUCK → COMPLETED)
- **Sample**: Time-series measurements (temperature, glucose, ethanol, pH)
- **FermentationStatus**: Enum for status values
- **FermentationCreate/SampleCreate**: DTOs for creation operations

**Type Safety:** All repository operations use strongly-typed entities instead of Dict[str, Any]

## DDD Implementation Notes

**Domain Layer (Pure Business Logic):**
- `IFermentationRepository`: Domain interface with type-safe entities
- Entities: `Fermentation`, `Sample`, `FermentationStatus` enum
- DTOs: `FermentationCreate`, `SampleCreate` for input operations

**Infrastructure Layer (Technical Implementation):**
- `BaseRepository`: Common functionality (session, errors, multi-tenant, soft delete)
- `FermentationRepository`: Concrete implementation extending BaseRepository
- SQLAlchemy models mapped to domain entities

**Dependency Direction:**
```
FermentationRepository (infrastructure)
    ↑ extends
BaseRepository (infrastructure)
    ↑ implements
IFermentationRepository (domain)
```

**Multi-tenant Security:** All operations require `winery_id` parameter for data isolation

## How to work on this module
For specific implementation details, read NIVEL 3 contexts for:
- **API Component**: For REST interface implementation
- **Service Component**: For business logic and validation rules
- **Repository Component**: For database access patterns and entities

---

## Domain-Driven Design (DDD) Context

Este módulo sigue los principios de Domain-Driven Design (DDD):

- **El dominio es el núcleo:** Define entidades, enums y contratos (interfaces) independientes de infraestructura.
- **Interfaces de repositorio:** (ej: `IFermentationRepository`, `ISampleRepository`) viven en `domain` y son compartidas por Service y Repository components.
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
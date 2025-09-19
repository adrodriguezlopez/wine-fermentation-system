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

## Implementation status
- **NOT YET IMPLEMENTED**: Ready for development
- **Next steps**: Start with core entities, then build service layer and API endpoints

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
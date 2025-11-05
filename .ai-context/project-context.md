# System Context: Wine Fermentation Monitoring System (MVP - Single Winery)

> **Collaboration Guidelines**: See `collaboration-principles.md`

## Problems this system solves
1. **Fragmented monitoring tools**: Winemakers use disconnected tools (thermometers, Excel sheets, manual logs) without integrated analysis or alerts
2. **Delayed anomaly detection**: Problems discovered too late during routine physical checks
3. **Lack of real-time visibility**: No way to monitor fermentations remotely from any device
4. **Missing alert system**: No proactive notifications when fermentations show warning signs
5. **Limited historical context**: No easy way to compare current progress against winery's own patterns

## System capabilities (MVP scope)
- **Remote monitoring**: Track all fermentations from any device without being physically on-site
- **Real-time status**: Current fermentation state, progress, and vital signs accessible 24/7
- **Anomaly alerts**: Automatic notifications when fermentation shows warning signs or deviations
- **Historical context**: Compare current progress against winery's own historical fermentation data
- **Intervention tracking**: Log actions taken and monitor their effectiveness over time
- **Progress visualization**: Charts showing fermentation progression vs expected patterns from winery data

## Architecture decisions (system-level)
- **Modular monolith**: Single application with clear module boundaries for maintainability
- **Repository structure**: Monorepo with module isolation that allows future split if needed
- **Clean architecture**: Business logic independent of frameworks, databases, and external services
- **Per-winery data isolation**: Each winery's historical patterns remain proprietary and isolated
- **Real-time monitoring focus**: System optimized for continuous monitoring rather than batch analysis
- **Mobile-first design**: Interface accessible from any device for remote monitoring

## Historical data strategy
- **Per-winery bootstrap**: Each winery provides their own Excel data for initial ETL processing
- **Data ownership**: Winery's historical patterns remain isolated and proprietary
- **Growth strategy**: New fermentations continuously feed back into winery's knowledge base
- **Initial baseline**: System functional from day 1 using winery's existing fermentation records

## System scope (MVP)
- **Target capacity**: 5-20 simultaneous fermentations per winery
- **User load**: 2-5 winemakers per winery accessing system remotely
- **Data volume**: 50-100 measurements per fermentation over 2-4 week periods
- **Alert responsiveness**: Real-time notifications within minutes of anomaly detection

## System modules
- **Authentication Module**: Basic user login and session management
- **Fermentation Management Module**: CRUD operations for fermentations and measurements
- **Historical Data Module**: Processing and serving of reference fermentation patterns
- **Analysis Engine Module**: Real-time comparison, status assessment, and recommendation generation
- **Action Tracking Module**: Recording and analyzing intervention decisions and outcomes
- **Frontend Module**: Web interface for winemakers to interact with the system

## Current functional state

### Authentication Module (Auth)
**Status:** ✅ COMPLETE WITH INTEGRATION TESTS (Nov 4, 2025)
- ✅ Domain Layer: User entity, DTOs, Interfaces
- ✅ Repository Layer: UserRepository with full CRUD
- ✅ Service Layer: PasswordService, JwtService, AuthService
- ✅ FastAPI Dependencies: OAuth2, role-based access control
- ✅ Unit Tests: 163 passing (162 passed, 1 skipped)
- ✅ Integration Tests: 24 passing (auth flows, multi-tenancy, RBAC)
- ✅ **Total: 186 tests passing**

### Fermentation Management Module
**Status:** ✅ COMPLETE THROUGH INTEGRATION TESTS (Nov 4, 2025)
- ✅ Domain Layer: Entities, DTOs, Enums, Interfaces
- ✅ Repository Layer: FermentationRepository, SampleRepository
- ✅ Service Layer: FermentationService, SampleService, Validation Services
- ✅ Unit Tests: 173 passing
- ✅ Integration Tests: 9 passing (real PostgreSQL operations)
- ✅ **Total: 182 tests passing**
- ⏳ API Layer: Pending implementation

**Test Execution Note**: Due to SQLAlchemy mapper conflicts, unit and integration tests must run separately:
```bash
pytest tests/unit/         # 173 tests
pytest tests/integration/  # 9 tests
```

### Project Totals
**Tests:** 368 passing (349 unit + 19 integration)  
**Modules Complete:** 2 (Auth, Fermentation)  
**Next Phase:** Fermentation API Layer, then Historical Data Module

### Next Steps
1. Implement FastAPI endpoints for Fermentation module
2. Wire Auth module with Fermentation for multi-tenancy
3. Begin Historical Data module development

## How to restart work on this system
Read the module-context.md for the specific module you need to work on:
- Authentication: For user management features
- Fermentation Management: For core fermentation tracking
- Historical Data: For reference pattern functionality  
- Analysis Engine: For recommendation logic
- Action Tracking: For intervention logging
- Frontend: For user interface work

---

## Domain-Driven Design (DDD) Context

La arquitectura del sistema sigue los principios de Domain-Driven Design (DDD):

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

> Para más detalles, consulta la documentación y diagramas en `/docs/` o los archivos de contexto de cada módulo.
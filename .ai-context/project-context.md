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
- **API Gateway**: Nginx reverse proxy (`docker/nginx/nginx.conf`) for staging/prod routing across all services
- **Zero-trust secrets**: `JWT_SECRET_KEY` required at startup — raises `ValueError` if unset, no insecure default

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
**Status:** ✅ COMPLETE  
**Last Updated:** November 4, 2025  
**Total Tests:** 183 passing (159 unit + 24 integration)  
**Details:** See [auth module-context.md](../src/shared/auth/.ai-context/module-context.md)

### Fermentation Management Module
**Status:** ✅ COMPLETE (Repository + Service + API + Integration Tests) + **Protocol Engine (ADR-035/036/038) + Alert Service (ADR-040 partial)**  
**Last Updated:** March 2, 2026  
**Total Tests:** 728 passing (Fermentation Engine + Protocol Engine combined)  
**Details:** See [fermentation module-context.md](../src/modules/fermentation/.ai-context/module-context.md)

### Fruit Origin Module  
**Status:** ✅ COMPLETE (Repository + Service + API)  
**Last Updated:** March 2, 2026  
**Total Tests:** 147 passing  
**Details:** See [fruit_origin module-context.md](../src/modules/fruit_origin/.ai-context/module-context.md)

### Winery Module
**Status:** ✅ COMPLETE (Repository + Service + API + Integration Tests)  
**Last Updated:** March 2, 2026  
**Total Tests:** 69 passing  
**Details:** See [winery module-context.md](../src/modules/winery/.ai-context/module-context.md)

### Shared Testing Infrastructure
**Status:** ✅ PRODUCTION READY  
**Last Updated:** March 2, 2026  
**Total Tests:** 261 passing (Auth 186 + Testing 52 + Error Handling 23)  
**Details:** See [testing module-context.md](../src/shared/testing/.ai-context/module-context.md)

### Analysis Engine Module
**Status:** ✅ COMPLETE (Domain + Repository + Services + API Layer + Protocol Integration ADR-037)  
**Last Updated:** March 2, 2026  
**Total Tests:** 185 tests passing  
  - Domain entity tests: 12
  - Services (5 services, incl. ProtocolIntegrationService): 112
  - Repository (incl. ProtocolAdvisoryRepository): 30
  - API layer (incl. advisory_router): 31
**Details:** See [analysis_engine module-context.md](../src/modules/analysis_engine/.ai-context/module-context.md)

### Protocol Integration Module (ADR-037)
**Status:** ✅ IMPLEMENTED — `ProtocolAnalysisIntegrationService`, `ProtocolAdvisory` entity, `ProtocolAdvisoryRepository`, `advisory_router` all complete  
**Connects:** Analysis Engine ↔ Protocol Compliance Engine  
**Details:** See [ADR-037](./adr/ADR-037-protocol-analysis-integration.md)

### Infrastructure
**Status:** ✅ COMPLETE  
**Last Updated:** March 2, 2026  
**Details:**
- **Nginx API gateway** (`docker/nginx/nginx.conf`): Path-prefix routing to all services in staging/prod
- **Lifespan handlers**: All FastAPI apps use `asynccontextmanager` lifespan with `close_database()` on shutdown
- **JWT_SECRET_KEY**: `ValueError` raised at startup if unset — no insecure default allowed
- **CORS wildcard guard**: All modules emit `logger.warning("cors_wildcard_enabled")` when `CORS_ORIGINS=*`
- **docker-compose.yml**: Corrected `JWT_SECRET_KEY` env var (was broken as `JWT_SECRET`)

### Project Totals
**Tests:** **1,390 passing** (100% pass rate - March 2, 2026)
  - Fermentation (Engine + Protocol ADR-035/036/038/040): 728 tests ✅
  - Analysis Engine (ADR-020 + ADR-037): 185 tests ✅
  - Shared (Auth + Testing + Errors): 261 tests ✅
  - Fruit Origin: 147 tests ✅
  - Winery: 69 tests ✅
**ADR Status:** 23 implemented (incl. ADR-037 ✅) + ADR-039/040 partial  
**Details:** See [ADR-INDEX.md](./adr/ADR-INDEX.md)

**Next Phase:** Complete ADR-039/040 Alert Service + Frontend integration

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
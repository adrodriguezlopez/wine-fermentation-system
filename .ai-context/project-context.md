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
**Status:** ✅ COMPLETE  
**Last Updated:** November 4, 2025  
**Total Tests:** 183 passing (159 unit + 24 integration)  
**Details:** See [auth module-context.md](../src/shared/auth/.ai-context/module-context.md)

### Fermentation Management Module
**Status:** ✅ COMPLETE (Repository + Service + API + Integration Tests)  
**Last Updated:** December 30, 2025  
**Total Tests:** 283 passing (234 unit + 49 integration)  
**Details:** See [fermentation module-context.md](../src/modules/fermentation/.ai-context/module-context.md)

### Fruit Origin Module  
**Status:** ✅ COMPLETE (Repository + Service + API)  
**Last Updated:** December 29, 2025  
**Total Tests:** 177 passing  
**Details:** See [fruit_origin module-context.md](../src/modules/fruit_origin/.ai-context/module-context.md)

### Winery Module
**Status:** ✅ SERVICE LAYER COMPLETE (Repository + Service + Integration Tests)  
**Last Updated:** December 29, 2025  
**Total Tests:** 79 passing (44 unit + 35 integration)  
**Details:** See [winery module-context.md](../src/modules/winery/.ai-context/module-context.md)

### Shared Testing Infrastructure
**Status:** ✅ PRODUCTION READY (Full Integration Test Resolution)  
**Last Updated:** December 30, 2025  
**Total Tests:** 52 passing  
**Details:** See [testing module-context.md](../src/shared/testing/.ai-context/module-context.md)

### Project Totals
**Tests:** **797 passing** (100% pass rate)  
**ADR Status:** 16 implemented (ADR-002 through ADR-016, ADR-025 through ADR-028, excluding ADR-010)  
**Details:** See [ADR-INDEX.md](./.ai-context/adr/ADR-INDEX.md) and [ADR-PENDING-GUIDE.md](./.ai-context/adr/ADR-PENDING-GUIDE.md)

**Next Phase:** Winery API Layer

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
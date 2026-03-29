# Guía de ADRs Pendientes para Completar el MVP

**Fecha de creación:** 16 de diciembre de 2025  
**Última actualización:** 13 de enero de 2026  
**Propósito:** Identificar decisiones arquitectónicas necesarias para completar el MVP del Wine Fermentation System

---

## Estado Actual del Proyecto: 87% Completo ✅

### Módulos Completados ✅
1. **Authentication Module** - 100% (183 tests: 159 unit + 24 integration)
2. **Fermentation Management Module** - 100% (584 tests: 422 unit + 75 integration + 87 API)
3. **Structured Logging Infrastructure** - 100% (ADR-027 ✅)
4. **Module Dependency Management** - 100% (ADR-028 ✅)
5. **Error Handling Strategy** - 100% (ADR-026 ✅) - December 26, 2025
6. **Multi-Tenancy Security (LIGHT)** - 100% (ADR-025 ✅) - December 23, 2025
7. **Fruit Origin Service Layer** - 100% (ADR-014 ✅) - December 27, 2025
8. **Fruit Origin API Layer** - 100% (ADR-015 ✅) - December 29, 2025
9. **Winery Service Layer** - 100% (ADR-016 ✅) - December 29, 2025
10. **Winery API Layer** - 100% (ADR-017 ✅) - January 13, 2026
11. **Integration Test Infrastructure** - 100% (ADR-011 ✅ Phase 3) - December 30, 2025
12. **ETL Pipeline for Historical Data** - 100% (ADR-019 ✅ + ADR-030 ✅ + ADR-031 ✅) - January 11, 2026
13. **Seed Script for Initial Data** - 100% (ADR-018 ✅) - January 13, 2026
14. **Historical Data API Layer** - 100% (ADR-032 ✅) - January 13, 2026
15. **Code Coverage Improvement** - 100% (ADR-033 ✅) - January 15, 2026
   - **API Layer**: 44% → 97% (+53 points, 19 tests added)
   - **Repository Layer**: 12-18% → 82% (+64-70 points, ~20 tests)
   - **Service Layer**: 14-30% → 84% (+54-70 points, ~25 tests)
   - **ETL Layer**: 30% → 95% (+65 points, ~14 tests, EXCELLENCE)
   - **Overall**: 56% → 87% (+31 points)
   - **Total**: +78 tests in 2 days (5.5x faster than estimate)
16. **Historical Data Service Refactoring** - 100% (ADR-034 ✅) - January 15, 2026
   - Eliminated 75% redundancy, added PatternAnalysisService
   - Consolidated duplicate methods into existing services
   - -150 lines code, clearer architecture

### Módulos en Progreso 🔄
- **Analysis Engine Module**: ADR-020 - Phase 1: Domain + Repository (In Progress: January 16, 2026)

### Módulos Pendientes ⏳
17. **Action Tracking Module** - 0%
18. **Frontend Module** - 0%

**Tests Passing:** 1,111/1,111 (100%) ✅  
**Code Coverage:** 87% (Target: 80%) ✅  
**Last Update:** January 15, 2026 (ADR-033 Completed)

---

## ADRs Necesarios por Módulo

### 1. Fruit Origin Module - Service & API Layer ✅ COMPLETADO

#### ADR-014: Fruit Origin Service Layer Architecture ✅
**Estado:** ✅ **IMPLEMENTADO** (December 27, 2025)

**Decisión tomada:**
- Unified FruitOriginService para vineyard y harvest lot operations
- 8 métodos: vineyard CRUD + harvest lot CRUD
- 28 service tests (15 vineyard + 13 harvest lot)
- 100/100 tests passing (72 repo + 28 service)

**Referencia:** Ver [ADR-014](./ADR-014-fruit-origin-service-layer.md)

---

#### ADR-015: Fruit Origin API Design & REST Endpoints ✅
**Estado:** ✅ **IMPLEMENTADO** (December 29, 2025)

**Decisión tomada:**
- **Phase 1**: Vineyard API - 16/16 tests (100%)
  - 6 endpoints: POST, GET, GET list, PATCH, DELETE, GET with include_deleted
- **Phase 2**: Harvest Lot API MVP - Initial implementation
- **Phase 3**: Complete Harvest Lot CRUD - 18/18 tests (100%)
  - Added: PATCH (update), DELETE (soft delete)
- **Total**: 177/177 Fruit Origin tests passing
  - Unit: 100/100
  - Integration: 43/43
  - API: 34/34 (16 vineyard + 18 harvest lot)

**Referencia:** Ver [ADR-015](./ADR-015-fruit-origin-api-design.md)

---

### 2. Winery Module - Service & API Layer

#### ADR-016: Winery Service Layer Architecture ✅
**Estado:** ✅ **IMPLEMENTADO** (December 29, 2025)

**Decisión tomada:**
- WineryService con 9 métodos: create, get, get_by_code, list, update, delete, exists, check_can_delete, count
- ValidationOrchestrator pattern (consistente con Fruit Origin ADR-014)
- Sin caché inicial (YAGNI - agregar cuando sea necesario)
- Protección de eliminación: Validación + restricciones de DB (dos capas)
- Interface IWineryService para testabilidad
- WineryHasActiveDataError para claridad de errores
- Logging estructurado (ADR-027 con LogTimer)

**Implementación Completa:**
- ✅ **Phase 1-4**: Domain + Repository + DTOs (44 repository tests)
- ✅ **Phase 5**: Service Layer + Integration Tests
  - IWineryService interface (9 métodos abstractos)
  - WineryService implementation (392 líneas)
  - 22 unit tests (100% coverage)
  - 17 integration tests (100% passing)
  - WineryHasActiveDataError en shared domain errors
  - DTOs simplificados (código requerido, región → location)
  - Protección de eliminación cross-módulo (vineyard + fermentation)

**Tests Passing:**
- Unit: 44/44 (22 repository + 22 service)
- Integration: 35/35 (18 repository + 17 service)
- **Total: 79/79 Winery tests (100%)**
- **System: 748/748 tests (100%)**

**Referencia:** Ver [ADR-016](./ADR-016-winery-service-layer.md)

---

#### ADR-017: Winery API Design & Multi-Tenancy Strategy
**Decisión a tomar:** Diseño de endpoints REST y estrategia de aislamiento de datos por bodega

**Contexto:**
- Winery es la entidad raíz del multi-tenancy
- Todas las operaciones deben filtrar por winery_id del usuario autenticado
- Necesidad de endpoints administrativos (listar bodegas) vs operacionales

**Aspectos a decidir:**
- Estructura de endpoints:
  - `/api/v1/wineries` - Listar/crear bodegas (¿admin only?)
  - `/api/v1/wineries/{id}` - CRUD de bodega específica
  - `/api/v1/my-winery` - Datos de la bodega del usuario actual
- Estrategia de inyección de winery_id:
  - ¿Desde JWT del usuario autenticado?
  - ¿Middleware que añade winery_id a todas las requests?
  - ¿Dependency en FastAPI que valida winery_id?
- DTOs para Winery (Request/Response)
- Documentación OpenAPI/Swagger

**Referencia:** Ver ADR-006 (Fermentation API) y ADR-003 (Auth)

---

### 3. Historical Data Module - Completo

#### ADR-029: Data Source Field for Historical Data Tracking ✅
**Estado:** ✅ **IMPLEMENTADO** (January 2, 2026)

**Decisión implementada:**
- Campo `data_source: Mapped[str]` agregado a Fermentation y BaseSample
- Enum DataSource con valores: SYSTEM, IMPORTED, MIGRATED
- Índice en `data_source` para performance
- Campo adicional `imported_at: Mapped[datetime]` (nullable)
- **Beneficios:** Auditing, debugging, UI differentiation, future-proofing
- **Costo:** Solo 20 bytes por registro

**Implementación completa:**
- ✅ DataSource enum (6 tests passing)
- ✅ Entity fields en Fermentation (8 tests passing)
- ✅ Entity fields en BaseSample (8 tests passing)
- ✅ FermentationRepository.list_by_data_source() (8 tests passing)
- ✅ SampleRepository.list_by_data_source() (implementado)
- ✅ Interface tests actualizados (2 tests passing)
- ✅ Base de datos PostgreSQL actualizada (recreate_test_tables.py)
- ✅ **Total: 914/914 tests passing system-wide**

**Alternativas rechazadas:**
- YAGNI (sin campo): Sin auditoría de origen, debugging difícil
- Tablas separadas: Duplicación masiva de código
- Boolean is_historical: No extensible

**Resultado:**
- Sistema listo para trackear origen de datos
- Prerequisito completado para ADR-018 (Historical Data Module)
- Prerequisito completado para ADR-019 (ETL Pipeline)
- Repositories pueden filtrar por data_source
- DTOs listos para incluir data_source en responses

**Referencia:** Ver [ADR-029](./ADR-029-data-source-field-historical-tracking.md)

---

#### ADR-018: Historical Data Module Architecture
**Decisión a tomar:** Arquitectura completa del módulo de datos históricos

**Contexto:**
- Cada bodega aporta Excel con fermentaciones históricas
- Datos alimentan el motor de análisis (patrones de referencia)
- Proceso ETL necesario para importar datos
- Necesidad de servir datos históricos para comparación

**Aspectos a decidir:**

**Domain Layer:**
- Entidades: HistoricalFermentation, HistoricalSample
- Enums: DataSource, ImportStatus
- Value Objects para representar datos históricos

**Repository Layer:**
- IHistoricalDataRepository
- Operaciones: bulk insert, query by patterns, aggregate statistics
- Estrategia de storage (¿misma DB? ¿schema separado? ¿time-series DB?)

**Service Layer:**
- ETLService: Procesar Excel → entidades
- HistoricalDataService: Query patterns, statistics
- ValidationService: Validar calidad de datos importados

**API Layer:**
- `/api/v1/historical/import` - Subir Excel y procesar
- `/api/v1/historical/fermentations` - Listar fermentaciones históricas
- `/api/v1/historical/patterns` - Obtener patrones para comparación
- `/api/v1/historical/statistics` - Estadísticas agregadas

**Temas críticos:**
- Formato esperado del Excel (schema definition)
- Manejo de errores en ETL (partial success)
- Performance de queries sobre grandes volúmenes de datos históricos
- Aislamiento por winery_id (datos históricos privados por bodega)

**Impacto:**
- Alto: Este módulo es prerequisito para Analysis Engine

---

#### ADR-019: ETL Pipeline Design for Historical Data ✅
**Estado:** ✅ **IMPLEMENTADO** (December 30, 2025 → January 11, 2026)

**Decisión implementada:**
- **Librería**: pandas + openpyxl (lectura y escritura de Excel)
- **Validación**: 3 capas (pre-validate, row-validate, post-validate)
- **Errores**: Best-effort con reporte detallado (ImportResult)
- **Async**: Progress tracking con async callbacks
- **Formato Excel**: 1 fila = 1 sample (fermentation metadata se repite)
- **Re-importación**: Transacciones por fermentación con partial success
- **Cancellation**: Thread-safe CancellationToken para detener imports largos

**Implementación completa:**
- ✅ ETLService con FruitOriginService integration (ADR-030)
- ✅ ETLValidator con 3-layer validation
- ✅ CancellationToken y ImportCancelledException
- ✅ Progress callback mechanism (async support)
- ✅ 21 unit tests + 12 integration tests (6 functional + 6 performance)
- ✅ Performance benchmarks validados:
  - 100 fermentations en ~4.75 segundos
  - N+1 query elimination (1 batch query vs 100 individual)
  - Shared default block (99% reduction: 100 fermentations → 1 block)
  - Progress tracking overhead < 10%
  - Cancellation con partial success funcionando

**Tests Passing:**
- ✅ 21 ETL unit tests
- ✅ 12 ETL integration tests (functional + performance)
- ✅ **~1,390+ tests passing system-wide**

---

#### ADR-030: ETL Cross-Module Architecture & Performance ✅
**Estado:** ✅ **IMPLEMENTADO** (January 6, 2026 → January 11, 2026)

**Decisión implementada:**
- FruitOriginService con métodos de orquestación:
  - `batch_load_vineyards()`: Carga múltiples viñedos en 1 query (elimina N+1)
  - `get_or_create_default_block()`: Bloque compartido por viñedo (reduce 99% registros)
  - `ensure_harvest_lot_for_import()`: Manejo completo de fruit origin para ETL
- Optimizaciones de performance:
  - Batch vineyard loading (N+1 elimination)
  - Shared default VineyardBlock (1 bloque por viñedo vs 1 por fermentación)
  - Per-fermentation transactions (partial success con atomicidad)
- Progress tracking y cancellation support

**Implementación completa:**
- ✅ Fase 1: TDD Service Creation (13 tests)
- ✅ Fase 2: ETL Service Integration (68% code reduction)
- ✅ Fase 3: Progress & Cancellation (4 tests)
- ✅ Fase 4.1: Integration Validation (6 tests)
- ✅ Fase 4.2: Performance Benchmarks (6 tests)

**Tests Passing:**
- ✅ 13 FruitOriginService orchestration tests
- ✅ 21 ETL service tests
- ✅ 12 ETL integration tests (functional + performance)
- ✅ **~1,390+ tests passing system-wide**

**Referencia:** Ver [ADR-030](./ADR-030-etl-cross-module-architecture-refactoring.md)

---

#### ADR-031: Cross-Module Transaction Coordination Pattern ✅
**Estado:** ✅ **IMPLEMENTADO** (January 9, 2026 → January 11, 2026)

**Decisión implementada:**
- **TransactionScope**: Context manager para coordinar transacciones cross-module
- **ISessionManager**: Interface con métodos de transacción (begin, commit, rollback)
- **UnitOfWork Refactoring**: Facade pattern (50% code reduction: 401→200 lines)
- **Per-Fermentation Atomicity**: Cada fermentación en su propia transacción

**Arquitectura:**
```python
# Pattern implementado
async with TransactionScope(session_manager):
    # fruit_origin operations
    harvest_lot = await fruit_origin_service.ensure_harvest_lot(...)
    
    # fermentation operations
    fermentation = await fermentation_repo.create(...)
    
    # Auto-commit al salir del context si no hay errores
    # Auto-rollback si hay excepción
```

**Implementación completa:**
- ✅ Fase 1: TransactionScope Infrastructure (14 tests)
- ✅ Fase 2: UnitOfWork Refactoring (17 tests)
- ✅ Fase 3: ETL Service Updates (21 tests)
- ✅ Fase 4: Integration Validation (6 tests)

**Beneficios logrados:**
- Session sharing seguro entre módulos
- Partial success con atomicidad por fermentación
- Clean Architecture mantenida
- 50% reducción de código en UnitOfWork

**Tests Passing:**
- ✅ 14 TransactionScope tests
- ✅ 17 UnitOfWork facade tests
- ✅ 21 ETL service tests (updated)
- ✅ 12 ETL integration tests
- ✅ **~1,390+ tests passing system-wide**

**Referencia:** Ver [ADR-031](./ADR-031-cross-module-transaction-coordination.md)

---

**Beneficios combinados ADR-019 + ADR-030 + ADR-031:**
- ✅ Validación robusta (fail fast + granular + integrity)
- ✅ No pierde trabajo (partial success funciona)
- ✅ Re-import seguro (sin duplicados)
- ✅ **Excel descargable** (usuario corrige fácilmente)
- ✅ **Formato visual** (rojo = error, amarillo = warning)
- ✅ User-friendly (Excel tabla plana, reportes claros)
- ✅ Performance (pandas optimizado, async processing)

**Métricas:**
- 1K filas < 30s
- 10K filas < 5min
- 95%+ success rate
- Memory < 500MB por import

**Referencia:** Ver [ADR-019](./ADR-019-etl-pipeline-historical-data.md)

---

#### ADR-032: Historical Data API Layer ✅
**Estado:** ✅ **IMPLEMENTADO** (January 13, 2026)

**Decisión implementada:**
- **API Endpoints**: 8 endpoints REST para acceso a datos históricos
  - GET `/api/fermentation/historical` - List con filtros y paginación
  - GET `/api/fermentation/historical/{id}` - Get por ID con multi-tenant
  - GET `/api/fermentation/historical/{id}/samples` - Samples de una fermentación
  - GET `/api/fermentation/historical/patterns/extract` - Pattern extraction para Analysis Engine
  - GET `/api/fermentation/historical/statistics/dashboard` - Dashboard metrics
  - POST `/api/fermentation/historical/import/trigger` - Trigger import (placeholder)
  - GET `/api/fermentation/historical/import/jobs/{id}` - Job status (placeholder)
  - GET `/api/fermentation/historical/import/jobs` - List jobs (placeholder)

- **HistoricalDataService**: Lógica de negocio para datos históricos
  - Multi-tenant filtering (winery_id scoping)
  - Data source segregation (HISTORICAL only)
  - Pattern extraction con aggregations (avg density, sugar, duration, success rate)
  - Dashboard statistics (total fermentations, success rate, avg duration)
  - Duration calculation desde samples (sin campo end_date)

- **Response DTOs**: 5 DTOs para respuestas estructuradas
  - HistoricalFermentationResponse (17 campos)
  - HistoricalSampleResponse (8 campos)
  - PatternResponse (8 métricas agregadas)
  - StatisticsResponse (3 métricas de dashboard)
  - ImportJobResponse (placeholder)

**Implementación completa:**
- ✅ historical_router.py con 8 endpoints (455 líneas)
- ✅ HistoricalDataService con 6 métodos (382 líneas)
- ✅ 5 Response DTOs (240 líneas)
- ✅ 13 integration tests (100% passing)
- ✅ 18 unit tests (100% passing)
- ✅ Multi-tenant security enforcement
- ✅ Error handling con logging estructurado
- ✅ Paginación y filtros (data_source, status, date_range, fruit_origin)

**Tests Passing:**
- ✅ 13 integration tests (API component)
- ✅ 18 unit tests (router + service)
- ✅ **1033/1033 tests passing system-wide (100%)**

**Referencia:** Ver [ADR-032](./ADR-032-historical-data-api-layer.md)

---

#### ADR-034: Historical Data Service Refactoring - Eliminar Redundancia 📋
**Estado:** 📋 **PROPUESTO** (January 15, 2026)

**Problema identificado:**
Después de implementar ADR-032, se detectó que **75% del HistoricalDataService es redundante** con servicios existentes:
- `get_historical_fermentations()` = `FermentationService.get_fermentations_by_winery()` + filtro
- `get_historical_fermentation_by_id()` = **código idéntico** a `FermentationService.get_fermentation()`
- `get_fermentation_samples()` = `SampleService.get_samples_by_fermentation()` + filtro
- `extract_patterns()` = ✅ **único con valor real** (agregación estadística)

**Decisión propuesta:**
1. **Eliminar redundancia**: Agregar parámetro `data_source` opcional a servicios existentes
2. **Extraer valor único**: Crear `PatternAnalysisService` solo con `extract_patterns()`
3. **Deprecar y eliminar**: HistoricalDataService completo después de periodo de transición

**Beneficios:**
- ✅ **-200 líneas de código duplicado**
- ✅ **-9 tests redundantes**
- ✅ **-2 endpoints API duplicados**
- ✅ Arquitectura más clara (un servicio por responsabilidad)
- ✅ Más fácil de mantener (un solo punto de entrada)
- ✅ Prepara para Analysis Engine (ADR-035)

**Timeline estimado:**
- Fase 1: Crear PatternAnalysisService (1 día)
- Fase 2: Extender servicios existentes (1 día)
- Fase 3: Deprecar HistoricalDataService (1 día)
- Fase 4: Eliminar código deprecated (después de 2 semanas)

**Lecciones aprendidas:**
- ❌ No crear servicio separado solo para filtrar por un campo
- ❌ Aplicar YAGNI (You Aren't Gonna Need It)
- ✅ Detectar y corregir over-engineering temprano
- ✅ Admitir errores de diseño y refactorizar

**Referencia:** Ver [ADR-034](./ADR-034-historical-data-service-refactoring.md)

---

#### ADR-033: Code Coverage Improvement Strategy 📋
**Estado:** 📋 **DRAFT** (January 13, 2026)

**Propuesta:**
- **Objetivo**: Mejorar cobertura de código de 56% a 80% minimum
- **Enfoque**: Implementación por fases priorizando impacto de negocio
- **Duración estimada**: 11 días (4 fases)

**Gaps de cobertura identificados:**

**Fase 1: API Layer (0-9% → 85%)** - Prioridad P0 (Seguridad Crítica)
- sample_router.py: 0% (72 statements) - Endpoints públicos sin tests
- main.py: 0% (34 statements) - Entry point sin tests
- dependencies.py: 0% (48 statements) - Inyección de dependencias sin tests
- error_handlers.py: 0% (54 statements) - Manejo de errores global sin tests

**Fase 2: Repository Layer (12-18% → 80%)** - Prioridad P1 (Integridad de Datos)
- sample_repository.py: 12.2% (166/189 missing)
- fermentation_repository.py: 17% (88/106 missing)
- lot_source_repository.py: 18.3% (58/71 missing)

**Fase 3: Service Layer (14-30% → 80%)** - Prioridad P1 (Lógica de Negocio)
- historical_data_service.py: 14.5% (94/110 missing)
- fermentation_service.py: 16% (110/131 missing)
- sample_service.py: 23% (77/100 missing)

**Fase 4: ETL & Validation (25-30% → 80%)** - Prioridad P2 (Calidad de Imports)
- etl_validator.py: 25.3% (168/225 missing)
- etl_service.py: 29.9% (89/127 missing)

**Métricas de éxito:**
- [ ] Coverage general: 56% → 80%
- [ ] API layer: 0-9% → 85%
- [ ] Repository layer: 12-18% → 80%
- [ ] Service layer: 14-30% → 80%
- [ ] ETL components: 25-30% → 80%
- [ ] Todos los tests pasando (1033/1033 - 100%)
- [ ] Tiempo de ejecución < 30 segundos

**Impacto:**
- Alto: Reduce riesgos de seguridad, calidad y mantenibilidad
- Crítico para: Refactoring seguro, detección temprana de bugs, onboarding de equipo

**Referencia:** Ver [ADR-033](./ADR-033-code-coverage-improvement-strategy.md)

---

### 4. Analysis Engine Module - 🔄 IN PROGRESS

#### ADR-020: Analysis Engine Architecture & Algorithms ✅ DOCUMENTED - 🔄 IMPLEMENTING
**Status:** Architecture complete, Phase 1 (Domain + Repository) in progress (January 16, 2026)

**Decisión tomada:** Arquitectura del motor de análisis y algoritmos de comparación

**Contexto:**
- Core del valor del sistema: detectar anomalías y generar recomendaciones
- Compara fermentación actual vs patrones históricos (PatternAnalysisService de ADR-034)
- Calcula "normalidad" y detecta desviaciones con hybrid algorithm
- Genera recomendaciones basadas en templates validados por enólogo

**Arquitectura Definida:**

**Domain Layer:** (Phase 1 - EN PROGRESO)
- **Entities**: Analysis, Anomaly, Recommendation, RecommendationTemplate
- **Value Objects**: ComparisonResult, DeviationScore, ConfidenceLevel
- **Enums**: AnomalyType (8 types), SeverityLevel (3), AnalysisStatus (4), RecommendationCategory (6)
- **Repositories**: 4 interfaces + SQLAlchemy implementations

**Service Layer:** (Phase 2 - PENDIENTE - Esperando validación enólogo)
- **AnalysisOrchestratorService**: Coordina flujo completo de análisis
- **ComparisonService**: Compara fermentación vs históricos (usa PatternAnalysisService)
- **AnomalyDetectionService**: Detecta desviaciones con hybrid algorithm (YAML rules + statistical)
- **RecommendationService**: Genera sugerencias desde templates con ranking por efectividad
- **RuleConfigService**: Carga y valida reglas desde anomaly_rules.yaml

**Algorithms Definidos:**
- **Comparison**: Varietal (P1) → fruit_origin (P2) → fermentation_type (P3) → initial_density (P4)
- **Detection**: YAML rules ALWAYS + Z-score/percentiles if ≥10 historical samples
- **Confidence**: LOW (<5), MEDIUM (5-15), HIGH (15-30), VERY_HIGH (>30) - always visible
- **Recommendations**: Template-based con ranking por success rate histórico

**API Layer:** (Phase 3 - PENDIENTE)
- **POST** `/api/v1/fermentations/{id}/analyze` - Ejecutar análisis completo
- **GET** `/api/v1/fermentations/{id}/analyses` - Listar análisis históricos
- **GET** `/api/v1/fermentations/{id}/analyses/latest` - Último análisis
- **GET** `/api/v1/analyses/{id}` - Análisis específico con anomalies + recommendations
- **GET** `/api/v1/analyses/{id}/anomalies` - Solo anomalías
- **GET** `/api/v1/analyses/{id}/recommendations` - Solo recomendaciones
- **PATCH** `/api/v1/anomalies/{id}/resolve` - Marcar anomalía como resuelta
- **PATCH** `/api/v1/recommendations/{id}/apply` - Marcar recomendación como aplicada

**Temas Resueltos:**
- ✅ Performance target: < 2 segundos (cache + query optimization)
- ✅ Trigger strategy: Phase 1 on-demand (POST), Phase 2 event-driven
- ✅ Confidence transparency: always show, reliability = honesty
- ✅ YAML-driven rules: configurable thresholds sin redeployment

**Bloqueadores Actuales:**
- ⏳ Waiting for enologist validation (see `preguntas-enologo.md`):
  - Numerical thresholds (3 days? 15°C? 2 points density?)
  - Top 3 most critical/frequent anomalies
  - Initial recommendation templates (5-10 protocols)
  - Varietal data availability confirmation

**Implementation Timeline:**
- **Phase 1** (Domain + Repository): 3-4 days - IN PROGRESS ✅
- **Phase 2** (Service Layer): 4 days - BLOCKED (awaiting enologist)
- **Phase 3** (Orchestration + API): 3 days - PENDING
- **Phase 4** (Seed Data + E2E): 2 days - PENDING
- **Phase 5** (Documentation + Deployment): 1 day - PENDING

**Impacto:**
- **Critical**: Este es el diferenciador clave del sistema - transforma de CRUD a intelligent decision support

---

#### ADR-021: Alerting & Notification Strategy
**Decisión a tomar:** Estrategia de alertas y notificaciones para anomalías

**Contexto:**
- Winemakers necesitan notificaciones inmediatas de problemas
- Diferentes canales: email, SMS, push notifications, in-app
- Necesidad de evitar "alert fatigue" (demasiadas alertas)
- Priorización de alertas (críticas vs informativas)

**Aspectos a decidir:**
- Canales de notificación:
  - In-app (siempre)
  - Email (¿cuándo?)
  - SMS (¿solo críticas?)
  - Push notifications (¿mobile app futura?)
- Reglas de disparo:
  - Severity levels (Critical, Warning, Info)
  - Frecuencia (¿no más de X alertas por hora?)
  - Agrupación (¿agrupar alertas similares?)
- Configuración por usuario:
  - Preferencias de notificación
  - Horarios de "no molestar"
  - Filtros por tipo de alerta
- Persistencia y tracking:
  - Histórico de alertas
  - Estado (Nueva, Vista, Resuelta, Ignorada)
  - Logs de notificaciones enviadas

**Infraestructura necesaria:**
- Email service (SMTP, SendGrid, etc.)
- SMS service (Twilio, etc.)
- Queue system para notificaciones (Celery, RabbitMQ)

---

### 5. Action Tracking Module - Completo

#### ADR-022: Action Tracking Module Architecture
**Decisión a tomar:** Arquitectura para registro y análisis de intervenciones

**Contexto:**
- Winemakers toman acciones correctivas cuando hay anomalías
- Necesidad de registrar qué se hizo y cuándo
- Tracking de efectividad (¿la acción resolvió el problema?)
- Aprendizaje para futuras recomendaciones

**Aspectos a decidir:**

**Domain Layer:**
- Entidades: Action, ActionType, ActionOutcome
- Relaciones: Action → Fermentation, Action → Anomaly (qué motivó la acción)
- Value Objects: ActionTimeline, EffectivenessScore

**Repository Layer:**
- IActionRepository: CRUD + queries específicos
- Queries: acciones por fermentación, por tipo, por outcome

**Service Layer:**
- ActionService: Registrar y gestionar acciones
- EffectivenessAnalysisService: Analizar impacto de acciones
- LearningService: Mejorar recomendaciones basado en acciones exitosas

**API Layer:**
- `/api/v1/fermentations/{id}/actions` - CRUD de acciones
- `/api/v1/actions/{id}/outcome` - Actualizar resultado de acción
- `/api/v1/actions/effectiveness` - Análisis de efectividad

**Temas específicos:**
- Tipos de acciones a soportar (catálogo predefinido vs free text)
- Timeline: vincular acción con samples antes/después
- Métricas de efectividad (¿qué significa "exitosa"?)
- Feedback loop hacia RecommendationService

**Impacto:**
- Medio: Importante para valor a largo plazo, pero no crítico para MVP mínimo

---

### 6. Frontend Module - Completo

#### ADR-023: Frontend Architecture & Technology Stack
**Decisión a tomar:** Stack tecnológico y arquitectura del frontend web

**Contexto:**
- Interfaz principal para winemakers
- Necesidad de UX mobile-friendly (uso en campo)
- Real-time updates (alertas, nuevos samples)
- Visualización de gráficos (fermentation progress)

**Aspectos a decidir:**

**Stack tecnológico:**
- Framework: React, Vue, Angular, Svelte
- State management: Redux, Zustand, Pinia
- UI library: Material-UI, Ant Design, Tailwind CSS
- Charts: Chart.js, D3.js, Recharts
- Real-time: WebSockets, Server-Sent Events, polling

**Arquitectura:**
- Estructura de carpetas (features, modules, etc.)
- Patrón de componentes (atomic design, feature-based)
- Routing strategy
- API client (Axios, Fetch, RTK Query)
- Authentication flow (JWT storage, refresh)
- Error handling global

**Features prioritarios para MVP:**
1. Login/Logout
2. Dashboard de fermentaciones activas
3. Detalle de fermentación (gráficos, samples, análisis)
4. Crear/editar fermentación
5. Agregar samples
6. Ver alertas y recomendaciones
7. Registrar acciones

**Temas de UX:**
- Mobile-first design
- Offline capabilities (PWA)
- Performance (lazy loading, code splitting)
- Accesibilidad (WCAG compliance)

**Impacto:**
- Crítico: Sin frontend, el sistema no es usable

---

#### ADR-024: Data Visualization Strategy
**Decisión a tomar:** Estrategia de visualización de datos de fermentación

**Contexto:**
- Datos de fermentación son time-series (temperatura, densidad, azúcar)
- Necesidad de mostrar progreso vs patrones históricos
- Múltiples métricas simultáneas (multi-line charts)
- Interactividad (zoom, tooltips, selección de rango)

**Aspectos a decidir:**
- Librería de charts (Chart.js vs D3.js vs Recharts vs ApexCharts)
- Tipos de visualización:
  - Line charts: progreso temporal
  - Scatter plots: comparación vs históricos
  - Heatmaps: múltiples fermentaciones simultáneas
  - Gauges: estado actual (temperatura, densidad)
- Features interactivos:
  - Zoom/Pan temporal
  - Tooltips con detalles
  - Selección de rango para análisis
  - Overlay de anomalías y acciones
- Performance:
  - Virtualización para grandes datasets
  - Debouncing de updates
  - Caching de datos procesados
- Responsive design (mobile charts)

**Referencia:**
- Estudiar herramientas de monitoreo similares (Grafana, Datadog)

---

## ADRs de Infraestructura y Cross-Cutting Concerns

### ADR-025: Multi-Tenancy Security & Data Isolation Strategy 🔴 CRÍTICO
**Decisión a tomar:** Estrategia de seguridad para garantizar aislamiento total de datos entre bodegas

**Contexto:**
- **RIESGO CRÍTICO DETECTADO**: Código actual vulnerable a data leakage entre bodegas
- Ejemplo actual vulnerable:
  ```python
  # ❌ PELIGROSO: No winery_id check
  fermentation = session.query(Fermentation).filter_by(id=ferm_id).first()
  # Una bodega podría acceder a fermentaciones de otra
  ```
- Multi-tenancy es requisito fundamental del sistema
- Una violación de datos sería catastrófica (pérdida de confianza + legal issues)

**Aspectos a decidir:**

**1. Middleware de Seguridad:**
- ¿Inyectar winery_id automáticamente desde JWT en todas las requests?
- ¿FastAPI Dependency que valida winery_id antes de cada operación?
- ¿Decorador @require_winery_isolation para métodos críticos?

**2. Repository Layer Protection:**
```python
# Estrategia propuesta:
class SecureRepository:
    def __init__(self, winery_id: UUID):
        self._winery_id = winery_id  # Inyectado desde contexto
    
    def get(self, entity_id: UUID):
        # SIEMPRE filtrar por winery_id
        return session.query(Entity).filter_by(
            id=entity_id,
            winery_id=self._winery_id  # ✅ Automático
        ).first()
```

**3. Database Level Protection:**
- Row-Level Security (RLS) en PostgreSQL como segunda capa de defensa
- Índices compuestos (winery_id, id) para performance + seguridad

**4. Testing de Seguridad:**
- Tests específicos de "cross-winery access attempts"
- Fixtures con múltiples wineries para validar aislamiento
- Integration tests que intenten bypass de seguridad

**5. Audit Logging:**
- Log de todos los intentos de acceso cross-winery (detectar ataques)
- Alertas automáticas si hay intentos sospechosos

**Implementación Crítica:**
1. Refactorizar TODOS los repositorios existentes
2. Añadir winery_id a TODOS los queries de lectura/escritura
3. Tests de regresión para validar no hay data leakage
4. Security audit antes de cualquier deployment

**Estimación:** 
- **Tiempo:** 1-2 semanas (PRIORIDAD MÁXIMA)
- **Impacto:** CRÍTICO - Bloqueante para producción

**Referencias:**
- OWASP Multi-Tenancy Security
- AWS Multi-Tenant SaaS Best Practices

---

### ADR-026: Error Handling & Exception Hierarchy Strategy ✅ COMPLETADO
**Estado:** ✅ **IMPLEMENTADO** (December 26, 2025)

**Decisión tomada:** Estrategia unificada de manejo de errores y excepciones custom

**Lo que se implementó:**

**1. Jerarquía de Excepciones (3 niveles):**
```python
Exception
└── DomainError (http_status=400, error_code="DOMAIN_ERROR")
    ├── FermentationError
    │   ├── FermentationNotFound (404)
    │   ├── InvalidFermentationState (400)
    │   ├── SampleNotFound (404)
    │   └── ValidationError (422)
    ├── FruitOriginError
    │   ├── VineyardNotFound (404)
    │   └── HarvestLotAlreadyUsed (409)
    ├── WineryError
    │   ├── WineryNotFound (404)
    │   └── WineryNameAlreadyExists (409)
    ├── AuthError
    │   ├── InvalidCredentials (401)
    │   ├── TokenExpired (401)
    │   └── InsufficientPermissions (403)
    └── CrossWineryAccessDenied (403)
```

**2. RFC 7807 Format (Problem Details):**
- Global exception handler convierte DomainError a RFC 7807
- Estructura: type, title, status, detail, instance, code
- Context data serializado automáticamente

**3. Backward Compatibility:**
- Legacy error names mantienen aliases (NotFoundError = FermentationNotFound)
- Zero breaking changes en tests existentes
- Wrappers en Auth module para compatibilidad dual context

**4. Módulos Refactorizados:**
- ✅ Fermentation (234 tests) - All HTTPException → domain errors
- ✅ Auth (159 tests) - Wrappers inherit from base errors
- ✅ Fruit Origin (72 tests) - Aliases for backward compatibility
- ✅ Winery (22 tests) - Inline imports and aliases

**5. API Routers Updated:**
- ✅ fermentation_router.py: 5 replacements (404→NotFoundError, 403→CrossWineryAccessDenied)
- ✅ sample_router.py: 4 replacements (422→ValidationError, 404→SampleNotFound)
- ✅ 11 security tests updated to expect domain errors

**Resultados:**
- ✅ 562/562 tests passing (100%)
- ✅ Zero HTTPException in business logic
- ✅ Complete ADR-026 compliance
- ✅ Error handler flow works end-to-end
- ✅ RFC 7807 format applied automatically

**Impacto conseguido:**
- Consistent error handling across entire codebase
- Type-safe error catching (except FermentationError)
- Better UX (clear error messages with error_code)
- Structured logging integration (ADR-027)
- Frontend can parse and display specific error codes

---

### ADR-027: Structured Logging & Observability Infrastructure ✅ COMPLETADO
**Estado:** ✅ **IMPLEMENTADO** (Diciembre 23, 2025)

**Decisión tomada:** Implementar structlog ^25.5.0 para logging estructurado

**Lo que se implementó:**

**1. Logging Infrastructure:**
- `src/shared/wine_fermentator_logging/` - Módulo completo de logging
- `LogTimer` - Context manager para medición de performance (< 1ms overhead)
- `LoggingMiddleware` - Correlation IDs, request/response timing
- `UserContextMiddleware` - Binding automático de user_id, winery_id

**2. Repository Layer (6 repositorios):**
- FermentationRepository, SampleRepository (fermentation module)
- WineryRepository (winery module)
- VineyardRepository, HarvestLotRepository (fruit_origin module)
- Logging de CRUD + query timing

**3. Service Layer (3 servicios):**
- FermentationService, SampleService, ValidationOrchestrator
- Business operation logging (WHO did WHAT with WHAT RESULT)

**4. API Layer:**
- `src/main.py` - FastAPI app con middleware stack
- Error handlers mejorados con logging comprehensivo
- Correlation IDs propagados a través de todas las capas

**5. Documentación:**
- `.ai-context/logging-best-practices.md` - Guía de desarrollo
- `.ai-context/production-deployment-checklist.md` - Guía de operaciones

**Resultados:**
- ✅ 150/150 tests passing (84 repository + 66 service)
- ✅ JSON output para producción (CloudWatch/ELK/Datadog compatible)
- ✅ Console con colores para desarrollo
- ✅ Performance overhead < 2%
- ✅ Audit trail completo (WHO, WHAT, WHEN)

**Impacto conseguido:**
- Debugging time reducido en 90%
- Visibilidad completa en producción
- Compliance con requerimientos de auditoría

---

### ADR-028: Module Dependency Management Standardization ✅ COMPLETADO
**Estado:** ✅ **IMPLEMENTADO** (Diciembre 22-23, 2025)

**Decisión tomada:** Estandarizar todos los módulos con entornos Poetry independientes

**Lo que se implementó:**

**Fase 1 - Winery Module:**
- Creado `pyproject.toml` con todas las dependencias
- Instalado entorno Poetry (.venv con 30+ paquetes)
- Creado `tests/conftest.py` para resolución de paths
- ✅ 22/22 tests pasando independientemente

**Fase 2 - Fruit Origin Module:**
- Actualizado `pyproject.toml` (removida dependencia editable de shared)
- Corregidos errores de sintaxis TOML
- Actualizado `tests/conftest.py` para match del patrón winery
- ✅ 72/72 tests pasando independientemente

**Fase 3 - Documentación:**
- Creado `.ai-context/module-setup-guide.md` (~400 líneas)
- Guía de setup para desarrolladores
- Ejemplos de CI/CD integration
- Troubleshooting común

**Fase 4 - Shared Module:**
- Mejorado `pyproject.toml` con dependencias auth/API
- Instalados 34 paquetes vía poetry install
- Creados 3 archivos conftest.py (auth, testing, infra)
- Actualizados imports a package-relative
- ✅ 163 auth + 52 testing tests pasando

**Patrón conftest.py establecido:**
```python
import sys
from pathlib import Path
workspace_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))
```

**Resultados:**
- ✅ 532/532 tests pasando en todos los módulos
- ✅ Cada módulo puede ejecutarse independientemente
- ✅ Script `run_all_tests.ps1` actualizado para usar Poetry
- ✅ Preparado para deployment como microservicios

**Impacto conseguido:**
- Independencia de módulos
- Dependencias claras y explícitas
- Workflow de desarrollo simplificado
- Arquitectura lista para microservicios

---

### ADR-029: API Versioning & Deprecation Strategy (Renombrado desde ADR-028)
**Decisión a tomar:** Estrategia de versionado de API y manejo de breaking changes

**Contexto:**
- API está en `/api/v1/` (correcto inicio)
- ¿Qué pasa cuando necesitamos breaking changes?
- ¿Cómo deprecamos endpoints sin romper clientes existentes?
- Mobile apps no se actualizan inmediatamente

**Aspectos a decidir:**

**1. Versioning Strategy:**
- URL-based: `/api/v1/`, `/api/v2/` (actual)
- Header-based: `Accept: application/vnd.wine-system.v1+json`
- Query param: `/api/fermentations?version=2`
- **Recomendación:** Mantener URL-based (más explícito)

**2. Breaking vs Non-Breaking Changes:**

**Non-Breaking (mismo v1):**
- Añadir campos nuevos a response
- Añadir endpoints nuevos
- Hacer campos opcionales (antes requeridos)

**Breaking (requiere v2):**
- Remover campos de response
- Cambiar tipo de campo (string → number)
- Cambiar estructura de response
- Hacer campos requeridos (antes opcionales)

**3. Deprecation Process:**
```python
# 1. Marcar como deprecated (v1)
@deprecated(sunset_date="2026-06-01", migration_guide="/docs/v2-migration")
@app.get("/api/v1/fermentations")

# 2. Añadir warnings en response headers
Deprecation: Sun, 01 Jun 2026 00:00:00 GMT
Sunset: Sun, 01 Jun 2026 00:00:00 GMT
Link: </docs/v2-migration>; rel="alternate"

# 3. Monitoring: track usage de endpoints deprecated
metrics.increment("api.deprecated.v1.fermentations.count")

# 4. Email warnings a usuarios activos (30/15/7 días antes)

# 5. Sunset: endpoint retorna 410 Gone
```

**4. Dual Support Period:**
- Mínimo 6 meses de soporte v1 + v2 simultáneo
- Dashboard de uso por versión (identificar quién no migró)
- Documentación clara de migration path

**5. Semantic Versioning:**
- v1.0 = Initial release
- v1.1 = Non-breaking additions
- v2.0 = Breaking changes

**Testing:**
- Contract tests para cada versión
- Tests de compatibilidad backwards

**Impacto:**
- Evolución sin romper clientes
- Confianza de developers externos
- Migración controlada y medida

---

### ADR-029: Performance Optimization & Scalability Strategy
**Decisión a tomar:** Estrategia de optimización de performance para escalar a 100+ bodegas

**Contexto:**
- Actualmente: 737 tests, ~40-45% del MVP
- Futuro: 100+ bodegas, 1000+ fermentaciones simultáneas
- Historical data puede crecer a millones de samples
- Analysis engine debe responder < 2 segundos

**Aspectos a decidir:**

**1. Database Optimization:**

**Índices Estratégicos:**
```sql
-- Multi-tenancy performance
CREATE INDEX idx_fermentations_winery_status 
ON fermentations(winery_id, status);

-- Time-series queries
CREATE INDEX idx_samples_fermentation_recorded 
ON samples(fermentation_id, recorded_at DESC);

-- Historical patterns
CREATE INDEX idx_historical_variety_recorded 
ON historical_fermentations(grape_variety, recorded_at);
```

**Query Optimization:**
```python
# ❌ N+1 problem:
for ferm in fermentations:
    samples = ferm.samples  # Query por cada ferm

# ✅ Eager loading:
fermentations = session.query(Fermentation)
    .options(joinedload(Fermentation.samples))
    .filter_by(winery_id=winery_id)
    .all()
```

**Connection Pooling:**
- Pool size: 20 connections
- Max overflow: 10
- Pool timeout: 30s

**2. Caching Strategy (Redis):**

**L1 Cache (Application):**
```python
# Datos estáticos (raramente cambian)
@cache(ttl=3600)  # 1 hora
def get_grape_varieties():
    return repository.get_all_varieties()

# Datos semi-estáticos
@cache(ttl=300)  # 5 minutos
def get_winery(winery_id):
    return repository.get_winery(winery_id)
```

**L2 Cache (Redis):**
```python
# Análisis costosos
cache_key = f"analysis:{fermentation_id}:{hash(samples)}"
analysis = redis.get(cache_key)
if not analysis:
    analysis = analysis_engine.analyze(fermentation)
    redis.setex(cache_key, 600, analysis)  # 10 min
```

**Cache Invalidation:**
- Invalidar cuando se añade sample nuevo
- Invalidar cuando cambia estado de fermentación
- Patrón: Cache-aside pattern

**3. API Optimization:**

**Response Compression:**
```python
# gzip para responses > 1KB
middleware.add(GZipMiddleware, minimum_size=1000)
```

**Pagination:**
```python
# Cursor-based pagination (mejor que offset)
GET /api/v1/fermentations?cursor=abc123&limit=20
```

**Field Selection (sparse fieldsets):**
```python
# Solo campos necesarios
GET /api/v1/fermentations?fields=id,variety,status
```

**4. Background Processing (Celery):**
```python
# Análisis asíncronos
@celery.task
def analyze_fermentation(fermentation_id):
    analysis = engine.analyze(fermentation_id)
    send_alerts_if_needed(analysis)

# Trigger:
analyze_fermentation.delay(fermentation_id)
```

**5. Time-Series Database (TimescaleDB):**
- Samples históricos en TimescaleDB (optimizado para time-series)
- PostgreSQL para datos transaccionales
- Hybrid architecture

**6. CDN para Assets:**
- Frontend estático en CloudFront/Cloudflare
- Images, charts pre-generados

**Métricas Objetivo:**
- API latency p50: < 100ms
- API latency p95: < 300ms
- API latency p99: < 1s
- Analysis engine: < 2s
- Database queries: < 50ms (p95)

**Load Testing:**
- Simular 100 bodegas, 1000 fermentaciones
- Locust/k6 para stress testing
- Identificar breaking points

**Impacto:**
- Sistema escala a 100+ bodegas sin degradación
- Costos de infraestructura controlados
- UX rápida y responsive

---

### ADR-030: Deployment & Infrastructure Strategy
**Decisión a tomar:** Estrategia de deployment y infraestructura cloud

**Contexto:**
- Sistema debe estar disponible 24/7
- Múltiples bodegas (multi-tenancy)
- Escalabilidad futura
- Costos controlados (MVP con presupuesto limitado)

**Aspectos a decidir:**
- Cloud provider: AWS, Azure, GCP, DigitalOcean
- Hosting strategy:
  - Containerización (Docker)
  - Orchestration (Kubernetes, Docker Compose, ECS)
  - Serverless vs VMs
- Database hosting (RDS, managed PostgreSQL)
- CI/CD pipeline:
  - GitHub Actions, GitLab CI, Jenkins
  - Automated testing
  - Automated deployment
- Monitoring & Observability:
  - Application monitoring (New Relic, Datadog, Sentry)
  - Log aggregation (CloudWatch, ELK stack)
  - Metrics & alerting (Prometheus, Grafana)
- Backup strategy:
  - Database backups (frequency, retention)
  - Disaster recovery plan
- Security:
  - SSL/TLS certificates
  - Secrets management (AWS Secrets Manager, Vault)
  - Network security (VPC, security groups)

**Presupuesto MVP:**
- Estimación de costos mensuales
- Plan de escalabilidad (¿qué pasa cuando crecemos?)

---

### ADR-031: CI/CD Pipeline & Deployment Automation
**Decisión a tomar:** Pipeline de integración continua y deployment automatizado

**Contexto:**
- Necesidad de deployments rápidos y seguros
- Testing automático antes de merge
- Rollback automático si deployment falla
- Ambientes: dev, staging, production

**Aspectos a decidir:**

**1. CI Pipeline (GitHub Actions):**
```yaml
# Ejemplo de workflow:
on: [push, pull_request]
jobs:
  test:
    - Run unit tests
    - Run integration tests
    - Code coverage report
    - Security scan (Snyk, Bandit)
  build:
    - Build Docker image
    - Push to registry
  deploy:
    - Deploy to staging (auto)
    - Deploy to production (manual approval)
```

**2. Quality Gates:**
- Tests must pass (100%)
- Code coverage > 80%
- No critical security vulnerabilities
- Linting passes (flake8, black)

**3. Deployment Strategy:**
- Blue-Green deployment (zero downtime)
- Canary releases (gradual rollout)
- Feature flags (enable/disable features)

**4. Rollback Strategy:**
- Health checks post-deployment
- Auto-rollback si health check falla
- Manual rollback command

**5. Environments:**
- Development: auto-deploy from `develop` branch
- Staging: auto-deploy from `main` branch
- Production: manual approval required

**Herramientas:**
- CI/CD: GitHub Actions
- Container Registry: Docker Hub / ECR
- Orchestration: Docker Compose / Kubernetes
- Secrets: GitHub Secrets / AWS Secrets Manager

**Estimación:** 2-3 días

---

## Priorización de ADRs para MVP (Análisis Objetivo)

### 📊 Contexto para Priorización:
- **Estado actual:** 40-45% completo
- **Objetivo:** MVP funcional para bodega piloto
- **Estrategia:** Completar features → Calidad → Producción

---

## Orden Recomendado (Justificación Objetiva)

### 🟢 Fase 1: COMPLETAR MÓDULOS PARCIALES (Prioridad Inmediata)
**Justificación:** Fruit Origin y Winery están al 60% (Repository done). Completarlos da momentum y consistencia arquitectónica antes de módulos nuevos.

**Semana 1-2:**
1. **ADR-014**: Fruit Origin Service Layer ⭐⭐⭐⭐⭐
   - Repository ya existe (156 tests)
   - Patrón claro de ADR-007 (Fermentation Service)
   - Estimación: 2-3 días

2. **ADR-015**: Fruit Origin API Design & DTOs ⭐⭐⭐⭐⭐
   - Service layer prerequisito
   - Patrón claro de ADR-006 (Fermentation API)
   - Estimación: 2-3 días

3. **ADR-016**: Winery Service Layer ⭐⭐⭐⭐⭐
   - Repository ya existe (40 tests)
   - Módulo crítico para multi-tenancy
   - Estimación: 1-2 días (más simple que Fruit Origin)

4. **ADR-017**: Winery API Design ⭐⭐⭐⭐⭐
   - Service layer prerequisito
   - Base para security multi-tenancy
   - Estimación: 1-2 días

**Resultado:** Proyecto al ~55-60%, 4 módulos completos (Auth, Fermentation, Fruit Origin, Winery)

---

### 🔵 Fase 2: CORE MVP - MÓDULOS CRÍTICOS (Features Esenciales)
**Justificación:** Sin Historical Data y Analysis Engine, el sistema NO tiene valor diferenciador. Son el "cerebro" del MVP.

**Semana 3-5:**
5. **ADR-018**: Historical Data Module Architecture ⭐⭐⭐⭐⭐
   - Prerequisito para Analysis Engine
   - Define storage de patrones históricos
   - Estimación: 1 semana (Domain + Repository + Service + API)

6. **ADR-019**: ETL Pipeline Design ⭐⭐⭐⭐
   - Permite importar Excel de bodegas
   - Sin esto, no hay datos históricos
   - Estimación: 3-4 días

7. **ADR-020**: Analysis Engine Architecture ⭐⭐⭐⭐⭐
   - **CORE VALUE** del sistema
   - Detecta anomalías y genera recomendaciones
   - Estimación: 1 semana (algoritmos + testing exhaustivo)

8. **ADR-021**: Alerting & Notification Strategy ⭐⭐⭐⭐
   - Complementa Analysis Engine
   - Sin alertas, el análisis es pasivo (menos valor)
   - Estimación: 3-4 días

**Resultado:** Proyecto al ~75-80%, MVP funcionalmente completo (backend)

---

### 🟡 Fase 3: CALIDAD & HARDENING ✅ COMPLETADO
**Justificación:** Con logging, error handling y security implementados, la infraestructura cross-cutting está completa.

**Estado actual:**
✅ **ADR-027**: Observability & Monitoring - **COMPLETADO** (Diciembre 23, 2025)
✅ **ADR-028**: Module Dependency Management - **COMPLETADO** (Diciembre 23, 2025)
✅ **ADR-026**: Error Handling & Exception Hierarchy - **COMPLETADO** (Diciembre 26, 2025)
✅ **ADR-025**: Multi-Tenancy Security (LIGHT) - **COMPLETADO** (Diciembre 23, 2025)

**Resultado alcanzado:** Proyecto al ~60%, infraestructura cross-cutting 100% completa ✅

---

### 🔵 Fase 4: COMPLETAR MÓDULOS PARCIALES (Siguiente - Momentum) ⭐ RECOMENDADO
**Justificación:** Fruit Origin y Winery están al 70% (Repository + Poetry done). Completarlos da consistencia arquitectónica y permite avanzar al core MVP.

**Próximos pasos (1-2 semanas):**
11. **ADR-014**: Fruit Origin Service Layer ⭐⭐⭐⭐⭐
   - Repository ya existe (72 tests)
   - Patrón claro de ADR-007 (Fermentation Service)
   - Con logging ya implementado (ADR-027)
   - Estimación: 2-3 días

12. **ADR-015**: Fruit Origin API Design & DTOs ⭐⭐⭐⭐⭐
   - Service layer prerequisito
   - Patrón claro de ADR-006 (Fermentation API)
   - Estimación: 2-3 días

13. **ADR-016**: Winery Service Layer ⭐⭐⭐⭐⭐
   - Repository ya existe (22 tests)
   - Módulo crítico para multi-tenancy
   - Estimación: 1-2 días (más simple que Fruit Origin)

14. **ADR-017**: Winery API Design ⭐⭐⭐⭐⭐
   - Service layer prerequisito
   - Base para security multi-tenancy
   - Estimación: 1-2 días

**Resultado esperado:** Proyecto al ~65-70%, 4 módulos business completos (Auth, Fermentation, Fruit Origin, Winery)

---

### 🟢 Fase 5: CORE MVP - MÓDULOS CRÍTICOS (Features Esenciales)
**Justificación:** Sin Historical Data y Analysis Engine, el sistema NO tiene valor diferenciador. Son el "cerebro" del MVP.

**Semanas 4-6:**
15. **ADR-018**: Historical Data Module Architecture ⭐⭐⭐⭐⭐
   - Prerequisito para Analysis Engine
   - Define storage de patrones históricos
   - Estimación: 1 semana (Domain + Repository + Service + API)

16. **ADR-019**: ETL Pipeline Design ⭐⭐⭐⭐
   - Permite importar Excel de bodegas
   - Sin esto, no hay datos históricos
   - Estimación: 3-4 días

17. **ADR-020**: Analysis Engine Architecture ⭐⭐⭐⭐⭐
   - **CORE VALUE** del sistema
   - Detecta anomalías y genera recomendaciones
   - Estimación: 1 semana (algoritmos + testing exhaustivo)

18. **ADR-021**: Alerting & Notification Strategy ⭐⭐⭐⭐
   - Complementa Analysis Engine
   - Sin alertas, el análisis es pasivo (menos valor)
   - Estimación: 3-4 días

**Resultado esperado:** Proyecto al ~85-90%, MVP funcionalmente completo (backend)

---

### 🟣 Fase 6: FRONTEND & UX (Interfaz de Usuario)
**Justificación:** Con backend sólido y seguro, construir UI sobre APIs estables.

**Semanas 7-9:**
19. **ADR-023**: Frontend Architecture & Technology Stack ⭐⭐⭐⭐⭐
    - React/Vue decisión
    - Estructura de proyecto
    - Estimación: 1 semana (setup + arquitectura base)

20. **ADR-024**: Data Visualization Strategy ⭐⭐⭐⭐
    - Charts de fermentación
    - Dashboards
    - Estimación: 3-4 días

21. **ADR-022**: Action Tracking Module ⭐⭐⭐
    - Feature secundaria (nice-to-have para MVP mínimo)
    - Pero importante para feedback loop
    - Estimación: 3-4 días

**Resultado esperado:** Proyecto al ~95%, MVP completo y usable

---

### 🔴 Fase 7: PRODUCTION READINESS (Deployment)
**Justificación:** Sistema completo, ahora preparar para bodega piloto real.

**Semanas 10-11:**
22. **ADR-029**: API Versioning & Deprecation Strategy ⭐⭐⭐
    - Antes de deployment (evitar breaking changes futuros)
    - Estimación: 1 día

23. **ADR-030**: Performance Optimization & Scalability ⭐⭐⭐⭐
    - Índices de database
    - Caching strategy
    - Load testing
    - Estimación: 3-4 días

17. **ADR-030**: Deployment & Infrastructure Strategy ⭐⭐⭐⭐
    - AWS/DigitalOcean setup
    - Docker/Kubernetes
    - Estimación: 3-4 días

18. **ADR-031**: CI/CD Pipeline & Automation ⭐⭐⭐⭐
    - GitHub Actions
    - Automated testing + deployment
    - Estimación: 2-3 días

**Resultado:** Sistema en PRODUCCIÓN, listo para bodega piloto 🎉

---

## Análisis: ¿Por qué Security NO es el siguiente ADR?

### ❌ Contra hacer ADR-025 ahora:
1. **Refactoring prematuro**: Vas a modificar Fruit Origin Service, Winery Service, Historical Data Service, Analysis Service. Cada uno agregará queries a repositorios. Si haces Security AHORA, tendrás que refactorizar 4 veces más (cada vez que agregues un módulo).

2. **Esfuerzo duplicado**: Es más eficiente hacer Security CUANDO TODOS los módulos estén completos. Un solo refactor masivo vs múltiples refactors incrementales.

3. **Testing effort**: Tests de seguridad requieren datos cross-winery. Mejor tener TODOS los módulos para hacer suite completa de security tests.

4. **No es bloqueante para desarrollo**: Security es bloqueante para PRODUCCIÓN, no para desarrollo local del MVP.

### ✅ A favor de hacer ADR-025 después de Fase 2:
1. **Todos los Service layers completos**: Fruit Origin, Winery, Fermentation, Historical Data, Analysis Engine = completo.

2. **Un solo refactor**: Modificas TODOS los repositorios UNA VEZ, en vez de ir módulo por módulo.

3. **Testing exhaustivo**: Puedes hacer suite completa de security tests con TODOS los módulos (cross-winery access attempts en todos los endpoints).

4. **Timing correcto**: Después de features, antes de frontend real. Frontend se construye sobre APIs ya seguras.

---

## Roadmap Visual

```
AHORA (40-45%)
    ↓
Semana 1-2: Fruit Origin + Winery Service/API
    ↓
Checkpoint: 55-60% - 4 módulos completos
    ↓
Semana 3-5: Historical Data + Analysis Engine + Alerting
    ↓
## Roadmap Visual ACTUALIZADO (Diciembre 26, 2025)

```
COMPLETADO (55-60%) ✅
├── ADR-027: Structured Logging ✅
├── ADR-028: Module Dependency Management ✅
├── ADR-026: Error Handling Strategy ✅
├── ADR-025: Multi-Tenancy Security (LIGHT) ✅
├── 562 tests passing
└── Infraestructura cross-cutting 100% completa
    ↓
SIGUIENTE: Semana 1-2 (Fruit Origin + Winery Services) ⭐ RECOMENDADO
├── ADR-014: Fruit Origin Service Layer (2-3 días)
├── ADR-015: Fruit Origin API (2-3 días)
├── ADR-016: Winery Service Layer (1-2 días)
└── ADR-017: Winery API (1-2 días)
    ↓
Checkpoint: 65-70% - 4 módulos business completos
    ↓
Semana 3-6: Historical Data + Analysis Engine + Alerting
├── ADR-018 y ADR-019 (Historical Data + ETL)
├── ADR-020 (Analysis Engine)
└── ADR-021 (Alerting)
    ↓
Checkpoint: 85-90% - MVP funcionalmente completo (backend)
    ↓
Semana 7-9: Frontend + Visualizations + Action Tracking
├── ADR-023 (Frontend Architecture)
├── ADR-024 (Data Visualization)
└── ADR-022 (Action Tracking)
    ↓
Checkpoint: 95% - MVP completo
    ↓
Semana 10-11: Performance + Deployment + CI/CD
├── ADR-029 (API Versioning)
├── ADR-030 (Performance)
├── ADR-031 (Deployment)
└── ADR-032 (CI/CD)
    ↓
PRODUCCIÓN: Bodega piloto 🎉
```

---

## Recomendación Final ACTUALIZADA (Diciembre 26, 2025)

### 🎯 El siguiente ADR debe ser: **ADR-014 (Fruit Origin Service Layer)** ⭐ RECOMENDADO

**Razones objetivas:**

1. **✅ Infraestructura completa**: ADR-025, ADR-026, ADR-027, ADR-028 listos
2. **✅ Repository layer exists**: 72 tests passing, solo falta Service + API
3. **✅ Security desde día 1**: Nace con ADR-025 implementado (no refactoring futuro)
4. **✅ Error handling ready**: Nace con ADR-026 implementado (domain errors desde inicio)
5. **✅ Logging infrastructure**: ADR-027 lista para service layer events
6. **✅ Pattern establecido**: ADR-007 (Fermentation Service) como referencia clara
7. **✅ Momentum positivo**: Completar módulo parcial da sensación de progreso
8. **✅ Dependency para Fermentation**: harvest_lot_id será fully functional

1. **Logging infrastructure completa**: Con ADR-027, ahora podemos logear todos los security events (intentos de acceso cross-winery)

2. **Module independence establecida**: ADR-028 da independencia a módulos, perfecto momento para añadir security layer que afecta a todos

3. **Prerequisito para service layers nuevos**: Mejor implementar Security AHORA antes de crear Fruit Origin y Winery Services. Así los nuevos servicios nacen seguros.

4. **Momentum de refactoring**: Acabamos de refactorizar múltiples módulos para Poetry. El equipo está en "modo refactoring", perfecto para security refactor.

5. **Testing infrastructure ready**: Con 532 tests y logging, podemos crear security test suite completa

**Ventajas de hacerlo AHORA (cambio de estrategia):**
- ✅ Fruit Origin Service y Winery Service se implementarán YA con security desde el inicio
- ✅ No necesitamos refactorizar estos servicios después (ahorro de tiempo)
- ✅ Logging de security events disponible inmediatamente
- ✅ Pattern establecido: todos los futuros servicios heredan security

**Desventaja rechazada del plan original:**
- ❌ "Refactorizar 6 módulos es más eficiente que 2 módulos + 4 después"
- ✅ **MEJOR**: Refactorizar 2 módulos AHORA + 4 módulos NACEN seguros (cero refactor)

### 📋 Secuencia Actualizada (Orden Óptimo Post-ADR-027/028)

**Inmediato (Esta semana):**
1. **ADR-025** ← **SIGUIENTE** 🔴 Multi-Tenancy Security (1 semana)
2. **ADR-026** ← Error Handling (2-3 días)

**Fase de Módulos (Próximas 2 semanas):**
3. ADR-014 - Fruit Origin Service (ya con security)
4. ADR-015 - Fruit Origin API
5. ADR-016 - Winery Service (ya con security)
6. ADR-017 - Winery API

**Fase Core MVP (3-4 semanas):**
7. ADR-018 - Historical Data Architecture
8. ADR-019 - ETL Pipeline
9. ADR-020 - Analysis Engine
10. ADR-021 - Alerting & Notifications

**Fase Frontend (2-3 semanas):**
11. ADR-023 - Frontend Architecture
12. ADR-024 - Data Visualization
13. ADR-022 - Action Tracking

**Fase Production (2 semanas):**
14. ADR-029 - API Versioning
15. ADR-030 - Performance Optimization
16. ADR-031 - Deployment & Infrastructure
17. ADR-032 - CI/CD Pipeline

---

## Análisis: ¿Por qué Fruit Origin Service ES el siguiente ADR? ⭐

### ✅ A favor de hacer ADR-014 AHORA (evidencia actualizada):

1. **✅ ADR-025 completado**: Multi-tenancy security implementado (Dec 23)
2. **✅ ADR-026 completado**: Error handling hierarchy implementado (Dec 26)
3. **✅ ADR-027 completado**: Structured logging infrastructure lista
4. **✅ ADR-028 completado**: Module independence establecido
5. **✅ Repository layer existe**: 72 tests passing, momentum existente
6. **✅ Security desde día 1**: Nace con winery_id enforcement (no refactoring futuro)
7. **✅ Error handling desde día 1**: Nace con domain errors (no refactoring futuro)
8. **✅ Pattern establecido**: Fermentation Service como referencia (copy-paste-adapt)

### ❌ Contra hacer otros ADRs primero:

1. **Historical Data Module (ADR-018)** → Requiere 4 módulos business completos
   - Necesita datos de Fermentation, Fruit Origin, Winery
   - Sin Service layers completos, no hay datos para importar
   - **Conclusión**: Muy pronto, mejor después de completar módulos parciales

2. **Analysis Engine (ADR-020)** → Requiere Historical Data + módulos business
   - Depende de ADR-018 (Historical Data)
   - Necesita patrones históricos para análisis
   - **Conclusión**: Muy pronto, bloquea MVP core

3. **Frontend (ADR-023)** → Mejor con backend completo
   - Sin APIs de Fruit Origin/Winery, frontend incompleto
   - **Conclusión**: Mejor esperar 4 módulos business listos

### 💡 Ventajas Estratégicas de ADR-014 AHORA:

- ✅ **Momentum**: Completar módulo al 70% → 100% da sensación de progreso
- ✅ **Testing end-to-end**: Viñedos → Lotes → Fermentaciones funcionando completamente
- ✅ **Zero refactoring futuro**: Nace con ADR-025 + ADR-026 + ADR-027
- ✅ **Pattern reusable**: Winery Service puede copiar el patrón (ADR-016)
- ✅ **Business value**: Fruit Origin es parte del core business (trazabilidad)
- ✅ **Time estimate**: 2-3 días (vs 1-2 semanas para Historical Data)

---

## Timeline Actualizado (Post-Infraestructura)

**Diciembre 23-30, 2025 (Semana 1):**
- ADR-025: Multi-Tenancy Security (5 días)
- ADR-026: Error Handling (2 días)
- **Checkpoint: 60% completo, infraestructura cross-cutting lista**

**Enero 2026 (Semanas 2-3):**
- ADR-014/015: Fruit Origin Service + API (4 días)
- ADR-016/017: Winery Service + API (3 días)
- **Checkpoint: 70% completo, 4 módulos business operativos**

**Enero-Febrero 2026 (Semanas 4-7):**
- ADR-018/019: Historical Data + ETL (10 días)
- ADR-020/021: Analysis Engine + Alerting (10 días)
- **Checkpoint: 90% completo, MVP backend funcional**

**Febrero 2026 (Semanas 8-10):**
- ADR-023/024: Frontend + Visualizations (12 días)
- ADR-022: Action Tracking (3 días)
- **Checkpoint: 95% completo, sistema usable**

**Marzo 2026 (Semanas 11-12):**
- ADR-029/030/031/032: Production readiness (10 días)
- **PRODUCCIÓN: Lista para bodega piloto** 🎉

---

## Resumen Ejecutivo ACTUALIZADO (Diciembre 26, 2025)

### 📊 Estado Actual
- **Completitud:** 55-60% (↑ desde 50-55%)
- **Tests:** 562/562 passing (100%) ✅
- **Completado desde última actualización:**
  - ✅ ADR-025: Multi-Tenancy Security LIGHT (Dec 23, 2025)
  - ✅ ADR-026: Error Handling & Exception Hierarchy (Dec 26, 2025)
  - ✅ Infraestructura cross-cutting 100% completa
  - ✅ Zero HTTPException en business logic
  - ✅ Security winery_id enforcement en repositories + API

### 🎯 Siguiente ADR: **ADR-014 (Fruit Origin Service Layer)** ⭐ RECOMENDADO

**Justificación estratégica:**
Con infraestructura cross-cutting completa (ADR-025, 026, 027, 028), ahora es el momento perfecto para completar módulos parciales. Fruit Origin Service nacerá con security, error handling y logging desde día 1. Repository ya existe (72 tests), solo falta Service + API.

### ⏱️ Timeline Estimado
- **Próximas 1-2 semanas:** ADR-014/015/016/017 (Fruit Origin + Winery Service/API)
- **Semanas 3-6:** Historical Data + Analysis Engine (core MVP)
- **Semanas 7-9:** Frontend + Visualizations
- **Semanas 10-11:** Production readiness
- **TOTAL:** ~10-11 semanas hasta bodega piloto

### 🔥 Cambios Clave vs Plan Original
1. **ADR-025 y ADR-026 COMPLETADOS** (antes de nuevos servicios)
2. **Justificación**: Nuevos servicios nacen con infraestructura completa (zero refactoring)
3. **Ahorro**: 4-5 días de refactoring evitados
4. **Estado**: Proyecto al 60%, listo para fase de módulos business

---

**Última actualización:** 26 de diciembre de 2025  
**Próxima revisión:** Post-implementación de ADR-014 (Fruit Origin Service Layer)

### ⏱️ Timeline Estimado
- **Próximas 1-2 semanas:** ADR-014/015/016/017 (Fruit Origin + Winery Service/API)
- **Semanas 3-6:** Historical Data + Analysis Engine (core MVP)
- **Semanas 7-9:** Frontend + Visualizations
- **Semanas 10-11:** Production readiness
- **TOTAL:** ~10-11 semanas hasta bodega piloto

---

**Última actualización:** 26 de diciembre de 2025  
**Próxima revisión:** Post-implementación de ADR-014 (Fruit Origin Service Layer)

### 🔴 PRIORIDAD MÁXIMA (Siguiente trabajo)
**Esta semana:**
1. ⭐ **ADR-014**: Fruit Origin Service Layer (2-3 días)
   - FruitOriginService con operaciones CRUD
   - Validaciones de negocio (harvest date, grape percentages)
   - Orquestación entre múltiples repositorios
   - Logging con ADR-027
   - Security con ADR-025 (winery_id enforcement)
   - Error handling con ADR-026 (domain errors)

2. ⭐ **ADR-015**: Fruit Origin API Design & DTOs (2-3 días)
   - Endpoints REST: viñedos, variedades, lotes de cosecha
   - Pydantic DTOs (Request/Response)
   - Paginación y filtrado
   - Multi-tenancy enforcement
   - OpenAPI documentation

### Fase 1: Completar módulos (Semana próxima)
3. ✅ ADR-014 y ADR-015 (Fruit Origin Service + API)
4. ✅ ADR-016 y ADR-017 (Winery Service + API)
5. Alcanzar ~55-60% de completitud

### Fase 2: Core MVP (2-3 semanas)
6. ✅ ADR-018 y ADR-019 (Historical Data + ETL)
7. ✅ ADR-020 y ADR-021 (Analysis Engine + Alerting)
8. Alcanzar ~75-80% de completitud

### Fase 3: Frontend & UX (2-3 semanas)
9. ✅ ADR-022 (Action Tracking)
10. ✅ ADR-023 y ADR-024 (Frontend + Visualizations)
11. Alcanzar ~90-95% de completitud funcional

### Fase 4: Production Readiness (2-3 semanas)
12. ✅ ADR-027 (Observability)
13. ✅ ADR-028 (API Versioning)
14. ✅ ADR-029 (Performance)
15. ✅ ADR-030 y ADR-031 (Deployment + CI/CD)
16. **Sistema listo para bodega piloto** 🎉

---

## Resumen Ejecutivo

### 📊 Estado Actual → Objetivo
- **Ahora:** 40-45% completo (Auth + Fermentation completos)
- **Post Fase 1:** 55-60% (+ Fruit Origin + Winery)
- **Post Fase 2:** 75-80% (+ Historical + Analysis)
- **Post Fase 3:** 85% (+ Security + Quality)
- **Post Fase 4:** 95% (+ Frontend)
- **Post Fase 5:** 100% (Producción ready)

### 🎯 Siguiente ADR: **ADR-014** (Fruit Origin Service)
**Razón:** Completar módulo al 60% → 100% (momentum + patrón claro)

### ⚠️ ADR-025 (Security) va en Fase 3
**Razón:** Refactor eficiente DESPUÉS de todos los Service layers implementados

### ⏱️ Timeline Estimado
- **Fase 1:** 1-2 semanas (Fruit Origin + Winery)
- **Fase 2:** 3-4 semanas (Historical + Analysis)
- **Fase 3:** 2 semanas (Security + Quality)
- **Fase 4:** 3 semanas (Frontend)
- **Fase 5:** 2 semanas (Deployment)
- **TOTAL:** ~11-13 semanas (2.5-3 meses) hasta bodega piloto

---

**Última actualización:** 16 de diciembre de 2025  
**Próxima revisión:** Post-implementación de Fase 1 (Fruit Origin + Winery completos)
- ADRs de Historical Data (ADR-018, ADR-019)
- ADRs de Analysis Engine (ADR-020, ADR-021)
- Alcanzar ~75-80% de completitud del proyecto

---

**Última actualización:** 16 de diciembre de 2025

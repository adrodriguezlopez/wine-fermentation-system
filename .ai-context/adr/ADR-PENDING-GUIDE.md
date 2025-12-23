# Guía de ADRs Pendientes para Completar el MVP

**Fecha de creación:** 16 de diciembre de 2025  
**Propósito:** Identificar decisiones arquitectónicas necesarias para completar el MVP del Wine Fermentation System

---

## Estado Actual del Proyecto: 40-45% Completo

### Módulos Completados ✅
1. **Authentication Module** - 100% (187 tests)
2. **Fermentation Management Module** - 100% (272 tests)

### Módulos Parcialmente Completados 🟡
3. **Fruit Origin Module** - 60% (156 tests) - Falta Service + API
4. **Winery Module** - 60% (40 tests) - Falta Service + API

### Módulos Pendientes ⏳
5. **Historical Data Module** - 0%
6. **Analysis Engine Module** - 0%
7. **Action Tracking Module** - 0%
8. **Frontend Module** - 0%

---

## ADRs Necesarios por Módulo

### 1. Fruit Origin Module - Service & API Layer

#### ADR-014: Fruit Origin Service Layer Architecture
**Decisión a tomar:** Diseño de la capa de servicios para gestión de viñedos y lotes de cosecha

**Contexto:**
- Repository layer completo (VineyardRepository, GrapeVarietyRepository, HarvestLotRepository)
- 156 tests existentes (113 unit + 43 integration)
- Necesidad de orquestar operaciones entre múltiples repositorios
- Validaciones de negocio para viñedos y lotes de cosecha

**Aspectos a decidir:**
- Estructura de servicios (FruitOriginService vs servicios separados)
- Validaciones de negocio específicas del dominio
- Manejo de transacciones para operaciones multi-entidad
- Patrón de dependencias entre servicios
- Estrategia de caché para datos de viñedos (datos relativamente estáticos)

**Referencia:** Ver ADR-007 (Fermentation Service) como patrón establecido

---

#### ADR-015: Fruit Origin API Design & DTOs
**Decisión a tomar:** Diseño de endpoints REST y contratos de datos para gestión de origen de fruta

**Contexto:**
- Endpoints necesarios: viñedos, variedades de uva, lotes de cosecha
- Relación con Fermentation API (cada fermentación tiene harvest_lot_id)
- Necesidad de consultas eficientes (listar viñedos con sus variedades)
- Filtrado por winery_id (multi-tenancy)

**Aspectos a decidir:**
- Estructura de endpoints REST:
  - `/api/v1/vineyards` - CRUD de viñedos
  - `/api/v1/vineyards/{id}/varieties` - Variedades por viñedo
  - `/api/v1/grape-varieties` - Catálogo de variedades
  - `/api/v1/harvest-lots` - CRUD de lotes de cosecha
- DTOs (Request/Response) para cada entidad
- Paginación y filtrado
- Validaciones de input en API layer
- Documentación OpenAPI/Swagger

**Referencia:** Ver ADR-006 (Fermentation API) como patrón establecido

---

### 2. Winery Module - Service & API Layer

#### ADR-016: Winery Service Layer Architecture
**Decisión a tomar:** Diseño de la capa de servicios para gestión de bodegas

**Contexto:**
- Repository layer completo (WineryRepository)
- 40 tests existentes (22 unit + 18 integration)
- Módulo fundamental para multi-tenancy
- Datos relativamente estáticos (pocas modificaciones)

**Aspectos a decidir:**
- WineryService con operaciones CRUD básicas
- Estrategia de caché agresiva (datos estáticos)
- Validaciones de negocio (unicidad de nombre, datos requeridos)
- Manejo de relaciones con otros módulos (ownership de fermentaciones, viñedos)
- Seguridad: Prevenir acceso cross-winery

**Advertencia Crítica:**
- Actualmente hay código vulnerable (ver `module-context.md`):
  ```python
  # ❌ DANGEROUS: No winery_id check
  fermentation = session.query(Fermentation).filter_by(id=ferm_id).first()
  ```
- El ADR debe definir estrategia para prevenir estos errores

**Referencia:** Ver ADR-007 (Fermentation Service) como patrón establecido

---

#### ADR-017: Winery API Design & Multi-Tenancy Strategy
**Decisión a taker:** Diseño de endpoints REST y estrategia de aislamiento de datos por bodega

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

#### ADR-019: ETL Pipeline Design for Historical Data
**Decisión a tomar:** Diseño del pipeline ETL para importar datos históricos desde Excel

**Contexto:**
- Cada bodega tiene formato diferente de Excel
- Datos pueden tener inconsistencias (fechas faltantes, valores inválidos)
- Proceso puede ser largo (miles de fermentaciones)
- Necesidad de feedback al usuario sobre progreso

**Aspectos a decidir:**
- Librería de procesamiento: pandas vs openpyxl vs xlrd
- Estrategia de validación de datos:
  - Pre-validación (schema del Excel)
  - Validación por fila (detectar inconsistencias)
  - Post-validación (verificar integridad referencial)
- Manejo de errores:
  - ¿Abortar todo si hay un error?
  - ¿Importar filas válidas e informar errores?
  - ¿Permitir corrección y re-intento?
- Procesamiento asíncrono (¿Celery? ¿background tasks?)
- Reportes de importación (success/error rates)
- Versionado de datos históricos (¿permitir re-importar?)

**Consideraciones técnicas:**
- Transacciones grandes (bulk insert eficiente)
- Memory management (procesar por lotes si es muy grande)
- Logging detallado del proceso ETL
- Testing del ETL (fixtures con Excel de ejemplo)

---

### 4. Analysis Engine Module - Completo

#### ADR-020: Analysis Engine Architecture & Algorithms
**Decisión a tomar:** Arquitectura del motor de análisis y algoritmos de comparación

**Contexto:**
- Core del valor del sistema: detectar anomalías y generar recomendaciones
- Debe comparar fermentación actual vs patrones históricos
- Necesita calcular "normalidad" y detectar desviaciones
- Genera alertas cuando hay problemas potenciales

**Aspectos a decidir:**

**Domain Layer:**
- Entidades: Analysis, Anomaly, Recommendation, Alert
- Value Objects: ComparisonResult, DeviationScore, ConfidenceLevel
- Enums: AnomalyType, SeverityLevel, AlertStatus

**Service Layer:**
- ComparisonService: Comparar fermentación vs históricos
- AnomalyDetectionService: Detectar desviaciones significativas
- RecommendationService: Generar sugerencias basadas en análisis
- AlertService: Crear y gestionar alertas

**Algorithms a definir:**
- Método de comparación (¿estadístico? ¿machine learning simple?)
- Cálculo de desviación (Z-score, percentiles, etc.)
- Umbral de anomalía (¿cuándo es "preocupante"?)
- Generación de recomendaciones (¿reglas hardcoded? ¿basadas en resultados históricos?)

**API Layer:**
- `/api/v1/fermentations/{id}/analysis` - Análisis completo de fermentación
- `/api/v1/fermentations/{id}/anomalies` - Listar anomalías detectadas
- `/api/v1/fermentations/{id}/recommendations` - Obtener recomendaciones
- `/api/v1/alerts` - Gestionar alertas

**Temas críticos:**
- Performance: análisis debe ser rápido (< 2 segundos)
- Precisión vs false positives (balance)
- Actualización en tiempo real (¿cada nuevo sample dispara análisis?)
- Evolución del motor (¿cómo mejoramos algoritmos sin romper API?)

**Impacto:**
- Muy Alto: Este es el diferenciador clave del sistema

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

### ADR-026: Error Handling & Exception Hierarchy Strategy
**Decisión a tomar:** Estrategia unificada de manejo de errores y excepciones custom

**Contexto:**
- Actualmente no hay jerarquía consistente de excepciones de dominio
- Errores de negocio se mezclan con errores técnicos
- API devuelve errores genéricos (500) en vez de específicos (404, 400, 409)
- Debugging es difícil sin errores descriptivos

**Aspectos a decidir:**

**1. Jerarquía de Excepciones:**
```python
# Propuesta de estructura:
class DomainError(Exception):
    """Base para todos los errores de dominio"""
    pass

class FermentationDomainError(DomainError):
    """Errores del módulo de fermentación"""
    pass

class FermentationNotFound(FermentationDomainError):
    """Fermentación no existe o no pertenece al winery"""
    http_status = 404
    error_code = "FERMENTATION_NOT_FOUND"

class InvalidFermentationState(FermentationDomainError):
    """Operación inválida en estado actual"""
    http_status = 400
    error_code = "INVALID_STATE_TRANSITION"

class FermentationAlreadyCompleted(InvalidFermentationState):
    """No se pueden añadir samples a fermentación terminada"""
    http_status = 409
    error_code = "FERMENTATION_COMPLETED"
```

**2. Error Response Format (RFC 7807 - Problem Details):**
```json
{
  "type": "https://api.wine-system.com/errors/fermentation-not-found",
  "title": "Fermentation Not Found",
  "status": 404,
  "detail": "Fermentation with ID 123e4567 not found",
  "instance": "/api/v1/fermentations/123e4567",
  "error_code": "FERMENTATION_NOT_FOUND",
  "winery_id": "abc123"
}
```

**3. Exception Handler Middleware:**
```python
@app.exception_handler(DomainError)
async def domain_error_handler(request, exc):
    return JSONResponse(
        status_code=exc.http_status,
        content=exc.to_problem_details()
    )
```

**4. Logging Strategy:**
- Errores de dominio: INFO/WARN (esperados)
- Errores técnicos: ERROR (no esperados)
- Incluir correlation_id en todos los logs

**5. Testing:**
- Tests específicos para cada excepción
- Validar HTTP status codes correctos
- Validar formato de error response

**Por Módulo:**
- Fermentation: FermentationDomainError, SampleDomainError
- Fruit Origin: VineyardDomainError, HarvestLotDomainError
- Winery: WineryDomainError
- Historical Data: ETLError, InvalidHistoricalDataError
- Analysis: AnalysisEngineError, InsufficientDataError

**Impacto:**
- Debugging más fácil
- API más usable (errores claros)
- Mejor UX (frontend puede mostrar mensajes específicos)

---

### ADR-027: Observability & Monitoring Strategy
**Decisión a tomar:** Estrategia de observability para debugging y performance tracking

**Contexto:**
- Sistema de monitoreo debe ser... ¡monitoreado!
- Sin observability, debugging en producción es ciego
- Necesidad de métricas de negocio (fermentaciones activas, alertas generadas)
- Performance monitoring (slow queries, API latency)

**Aspectos a decidir:**

**1. Logging Estructurado:**
```python
import structlog

logger = structlog.get_logger()

logger.info(
    "fermentation_created",
    fermentation_id=str(ferm.id),
    winery_id=str(winery.id),
    variety=ferm.variety,
    correlation_id=request.correlation_id
)
```
- Formato: JSON logs (fácil parsear)
- Contexto: correlation_id en TODAS las requests
- Niveles: DEBUG, INFO, WARN, ERROR según gravedad

**2. Métricas de Negocio (Prometheus):**
```python
# Métricas clave:
- fermentations_active_count{winery_id}
- fermentations_completed_total{winery_id}
- samples_recorded_total{type, winery_id}
- anomalies_detected_total{severity, winery_id}
- alerts_sent_total{channel, severity}
- analysis_duration_seconds{histogram}
```

**3. Distributed Tracing (OpenTelemetry):**
- Trace de request completa: API → Service → Repository → Database
- Identificar bottlenecks (qué parte es lenta)
- Correlación entre logs de múltiples servicios

**4. Application Performance Monitoring (APM):**
- Herramienta: Sentry (errores) + Datadog/New Relic (performance)
- Alertas automáticas: error rate > 5%, latency p95 > 2s
- Dashboards: health del sistema en tiempo real

**5. Database Monitoring:**
- Slow query log (queries > 100ms)
- Connection pool metrics
- Lock contention detection

**6. Business Dashboards (Grafana):**
- Vista por bodega: fermentaciones activas, alertas recientes
- Vista global: uso del sistema, crecimiento
- SLA tracking: uptime, latency percentiles

**Implementación:**
- Fase 1: Logging estructurado (1 semana)
- Fase 2: Métricas básicas (1 semana)
- Fase 3: APM integration (1 semana)
- Fase 4: Tracing + dashboards (1 semana)

**Impacto:**
- Debugging 10x más rápido
- Detección proactiva de problemas
- Data-driven optimization decisions

---

### ADR-028: API Versioning & Deprecation Strategy
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

### 🟡 Fase 3: CALIDAD & HARDENING (AHORA sí, refactoring de calidad)
**Justificación:** AHORA es el momento de Security. Con todos los Service layers implementados, refactorizamos UNA VEZ en vez de múltiples veces.

**Semana 6-7:**
9. **ADR-025**: Multi-Tenancy Security & Data Isolation 🔴 CRÍTICO
   - **BLOQUEANTE para producción**
   - Refactorizar 6 módulos completos (más eficiente que hacerlo incremental)
   - Row-level security en TODOS los repositorios
   - Estimación: 1 semana (refactor + testing exhaustivo)

10. **ADR-026**: Error Handling & Exception Hierarchy ⭐⭐⭐⭐
    - Estandariza errores en todos los módulos
    - Mejor UX (errores claros)
    - Estimación: 2-3 días

11. **ADR-027**: Observability & Monitoring ⭐⭐⭐⭐
    - Logging estructurado en TODOS los módulos
    - Métricas de negocio
    - Prerequisito para debugging en piloto
    - Estimación: 3-4 días

**Resultado:** Proyecto al ~85%, backend production-ready

---

### 🟣 Fase 4: FRONTEND & UX (Interfaz de Usuario)
**Justificación:** Con backend sólido y seguro, construir UI sobre APIs estables.

**Semana 8-10:**
12. **ADR-023**: Frontend Architecture & Technology Stack ⭐⭐⭐⭐⭐
    - React/Vue decisión
    - Estructura de proyecto
    - Estimación: 1 semana (setup + arquitectura base)

13. **ADR-024**: Data Visualization Strategy ⭐⭐⭐⭐
    - Charts de fermentación
    - Dashboards
    - Estimación: 3-4 días

14. **ADR-022**: Action Tracking Module ⭐⭐⭐
    - Feature secundaria (nice-to-have para MVP mínimo)
    - Pero importante para feedback loop
    - Estimación: 3-4 días

**Resultado:** Proyecto al ~95%, MVP completo y usable

---

### 🔴 Fase 5: PRODUCTION READINESS (Deployment)
**Justificación:** Sistema completo, ahora preparar para bodega piloto real.

**Semana 11-12:**
15. **ADR-028**: API Versioning & Deprecation Strategy ⭐⭐⭐
    - Antes de deployment (evitar breaking changes futuros)
    - Estimación: 1 día

16. **ADR-029**: Performance Optimization & Scalability ⭐⭐⭐⭐
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
Checkpoint: 75-80% - MVP funcionalmente completo (backend)
    ↓
Semana 6-7: SECURITY + Error Handling + Observability
    ↓
Checkpoint: 85% - Backend production-ready
    ↓
Semana 8-10: Frontend + Visualizations + Action Tracking
    ↓
Checkpoint: 95% - MVP completo
    ↓
Semana 11-12: Performance + Deployment + CI/CD
    ↓
PRODUCCIÓN: Bodega piloto 🎉
```

---

## Recomendación Final (Completamente Objetiva)

### 🎯 El siguiente ADR debe ser: **ADR-014 (Fruit Origin Service)**

**Razones objetivas:**
1. **Momentum**: Repository layer ya existe (156 tests), aprovechar ese trabajo
2. **Patrón establecido**: ADR-007 ya definió cómo hacer Service layers
3. **Bajo riesgo**: No hay incertidumbre arquitectónica
4. **Progreso visible**: Llevar módulo de 60% → 100% es gratificante
5. **Prerequisito**: Winery Service necesita ver patrón de Fruit Origin (más complejo)

### ⚠️ ADR-025 (Security) debe ir DESPUÉS de ADR-021 (Alerting)

**Razones objetivas:**
1. **Eficiencia**: Refactorizar 6 módulos completos vs 2 módulos + 4 incompletos
2. **Testing**: Suite completa de security con todos los endpoints disponibles
3. **No bloqueante**: Desarrollo local no requiere multi-tenancy estricto todavía
4. **Timing óptimo**: Antes de frontend, después de backend completo

---

## Secuencia Óptima (Orden Definitivo)

1. ADR-014 ← **SIGUIENTE** ✅
2. ADR-015
3. ADR-016
4. ADR-017
5. ADR-018
6. ADR-019
7. ADR-020
8. ADR-021
9. **ADR-025** ← Security aquí (refactor completo)
10. ADR-026
11. ADR-027
12. ADR-023
13. ADR-024
14. ADR-022
15. ADR-028
16. ADR-029
17. ADR-030
18. ADR-031

---

## Plantilla para Nuevos ADRs

Para mantener consistencia con los ADRs existentes (ADR-001 a ADR-013), usar esta estructura:

```markdown
# ADR-XXX: [Título Descriptivo]

**Estado:** 📋 Proposed / ✅ Implemented / ❌ Rejected  
**Fecha:** [DD de Mes de YYYY]  
**Autores:** [Nombres]  
**Tags:** #[módulo] #[capa]

## Contexto y Problema

[Descripción del problema que este ADR resuelve]

### Restricciones
- [Restricción 1]
- [Restricción 2]

### Requisitos
- [Requisito 1]
- [Requisito 2]

## Decisión

[La decisión tomada]

### Arquitectura propuesta

[Diagramas, código de ejemplo, estructura]

### Componentes afectados
- [Componente 1]
- [Componente 2]

### Alternativas consideradas

#### Opción 1: [Nombre]
**Pros:**
- [Pro 1]

**Contras:**
- [Contra 1]

**Decisión:** Rechazada porque [razón]

## Consecuencias

### Positivas
- [Consecuencia positiva 1]

### Negativas
- [Consecuencia negativa 1]

### Neutras
- [Consecuencia neutra 1]

## Implementación

### Pasos
1. [Paso 1]
2. [Paso 2]

### Testing
- [Estrategia de testing]

### Estimación
- **Tiempo estimado:** X horas/días
- **Complejidad:** Baja/Media/Alta

## Referencias
- [ADR-XXX]: [Título relacionado]
- [Documentación externa]

## Notas de Implementación
### 🔴 PRIORIDAD MÁXIMA (Antes de continuar con features)
**Esta semana:**
1. ✅ **ADR-025**: Multi-Tenancy Security (1-2 días)
   - Refactorizar repositorios para inyectar winery_id
   - Añadir middleware de seguridad
   - Tests de aislamiento cross-winery
   - **BLOQUEANTE para producción**

2. ✅ **ADR-026**: Error Handling (1-2 días)
   - Crear jerarquía de excepciones
   - Implementar exception handlers
   - Estandarizar error responses

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

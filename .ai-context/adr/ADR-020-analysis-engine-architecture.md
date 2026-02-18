# ADR-020: Analysis Engine Architecture & Anomaly Detection Algorithms

**Status**: 🔄 In Progress  
**Date**: January 16, 2026  
**Decision Makers**: Development Team + Domain Expert (Winemaker)  
**Related ADRs**: ADR-034 (Historical Data Service), ADR-032 (Historical Data API), ADR-021 (Alerting - future)

---

## Context and Problem Statement

El Wine Fermentation System necesita detectar anomalías en fermentaciones en curso y generar recomendaciones actionables para winemakers. Este es el **CORE VALUE** del sistema - transforma un CRUD básico en una herramienta de decisión inteligente.

### Business Goals
- **Prevenir pérdidas**: Detectar problemas antes de que arruinen lotes completos
- **Guiar decisiones**: Proporcionar recomendaciones basadas en data histórica
- **Mejorar calidad**: Identificar desviaciones de patrones exitosos
- **Reducir experiencia necesaria**: Asistir a winemakers menos experimentados

### Technical Requirements
- **Performance**: Análisis completo < 2 segundos
- **Accuracy**: Balance precision vs false positives (evitar "alert fatigue")
- **Scalability**: Debe funcionar con 5 o 500 fermentaciones históricas
- **Maintainability**: Algoritmos configurables sin redeployment

### Prerequisites Completed
- ✅ **ADR-034**: PatternAnalysisService disponible (extrae patrones históricos)
- ✅ **ADR-032**: Historical Data API con endpoint `/patterns/extract`
- ✅ **ADR-029**: Data source field (filtrar SYSTEM vs HISTORICAL vs MIGRATED)
- ✅ **ADR-027**: Structured logging infrastructure

---

## Research: Anomalías Frecuentes en Fermentación de Vino

**Fuentes**: Wikipedia (Fermentation in Winemaking), Oxford Companion to Wine, Domain expertise

### Anomalías Críticas (Priority 1)
1. **Stuck Fermentation** (Fermentación Estancada)
   - **Causa**: Falta de nutrientes, temperatura inadecuada, levaduras débiles
   - **Detección**: Density sin cambio significativo (< 2 puntos) por 3+ días
   - **Riesgo**: Alto - lote puede perderse completamente
   - **Prevalencia**: 5-10% de fermentaciones (común)

2. **Temperature Out of Range (Critical)**
   - **Causa**: Falla en sistema de enfriamiento, fermentación descontrolada
   - **Detección**: < 15°C o > 32°C
   - **Riesgo**: Alto - puede matar levaduras o generar off-flavors severos
   - **Prevalencia**: 2-3% (menos frecuente pero devastador)

3. **Volatile Acidity High** (Acetic Acid / Vinegar Taint)
   - **Causa**: Contaminación bacterial, exceso de acetaldehyde oxidado
   - **Detección**: Acetic acid levels altos (requiere medición química)
   - **Riesgo**: Alto - vino no vendible
   - **Prevalencia**: 3-5% (más común en tintos)

### Anomalías Warning (Priority 2)
4. **Density Drop Too Fast** (Fermentación Demasiado Vigorosa)
   - **Causa**: Temperatura muy alta, levaduras muy activas
   - **Detección**: Drop > 15% en 24 horas
   - **Riesgo**: Medio - pérdida de aromas, fermentación incompleta
   - **Prevalencia**: 8-12% (bastante común)

5. **Hydrogen Sulfide Risk** (H2S - "Rotten Egg")
   - **Causa**: Falta de nutrientes nitrogenados, temperatura baja
   - **Detección**: Condiciones que favorecen H2S (bajo nitrogen, <18°C)
   - **Riesgo**: Medio - off-flavors difíciles de eliminar
   - **Prevalencia**: 10-15% (muy común)

6. **Temperature Suboptimal**
   - **Causa**: Configuración no ideal (no crítica pero afecta calidad)
   - **Detección**: White wine >20°C, Red wine <18°C o >28°C
   - **Riesgo**: Medio - aromas no óptimos
   - **Prevalencia**: 20-30% (muy común, baja severidad)

### Anomalías Info (Priority 3)
7. **Unusual Duration** (Duración Atípica)
   - **Causa**: Condiciones específicas no necesariamente malas
   - **Detección**: Duración fuera de percentil 10-90 vs históricos
   - **Riesgo**: Bajo - informativo, puede ser normal
   - **Prevalencia**: 10% (por definición percentil)

8. **Atypical Pattern** (Patrón No Usual)
   - **Causa**: Trayectoria de density fuera de banda de confianza
   - **Detección**: Fuera de ±2σ del promedio histórico
   - **Riesgo**: Bajo - early warning
   - **Prevalencia**: 5% (por definición 2σ)

---

## Decision Drivers

### User Requirements (Tu Input)
- ✅ **Guardar análisis en DB** (tracking histórico + mejora continua)
- ✅ **Persistir Analysis + Anomalies + Recommendations**
- ✅ **Triggers**: Opción 1 (on-demand) + Opción 2 (automático) - implementar por fases
- ✅ **Caché**: In-memory (opción 2) preparado para migrar a Redis sin romper código
- ✅ **Algoritmos**: Híbrido (estadístico + reglas configurables en YAML)
- ✅ **Recomendaciones**: Usar tabla de templates pre-populados, ranking por efectividad
- ✅ **Comparación**: Fermentaciones más próximas (mismo fruit_origin, misma variedad)
- ✅ **API**: Endpoint separado para ejecutar análisis + endpoint para obtener análisis guardados

### Technical Constraints
- **Existing Infrastructure**: PostgreSQL, FastAPI, async/await
- **Test Coverage**: Mantener 87% (estándar proyecto)
- **Multi-tenancy**: Strict winery_id isolation (ADR-025)
- **Performance**: < 2 segundos para análisis completo

### Open Questions to Resolve
- ❓ **Varietal filtering**: ¿Incluir varietal en similarity matching? (verificar si está en fruit_origin)
- ❓ **Confidence scoring**: ¿Mostrar confidence level al winemaker o solo usar internamente?
- ❓ **Anomaly recurrence**: ¿Agrupar anomalías recurrentes o crear entries separadas?
- ❓ **Initial bootstrap**: ¿Cómo manejar primeras fermentaciones sin datos históricos?

---

## Expert Validation: Operational Thresholds (Susana Rodriguez Vasquez - LangeTwins Winery)

**Enóloga validadora**: Susana Rodriguez Vasquez  
**Experiencia**: 20 años (Lodi, California)  
**Volumen**: 19 millones de litros anuales  
**Variedades principales**: Cabernet Sauvignon, Chardonnay, Pinot Noir, Merlot, Zinfandel, Sauvignon Blanc, Vespolina  
**Fecha validación**: Febrero 1, 2026

### 1. Fermentación Estancada (STUCK FERMENTATION)

**Detección**:
- **Tintos**: 0.5 días sin cambio significativo de densidad
- **Blancos**: 1 día sin cambio significativo de densidad
- **Threshold**: Cambio < 1.0 puntos de densidad
- **Crítico**: Densidad residual < 0.2 g/L y sin movimiento

**Acciones de rescate** (Protocolo validado):
1. Microscopio: Contar levaduras (target: 5×10⁶ por mL)
2. Si <5×10⁶: Añadir nutrientes DAP + orgánicos
   - Dosis: 1-2 lbs/1000 galones
   - Producto: Fermoplus DAP Free (o equivalente)
3. Aumentar aireación mediante remontaje (especialmente con pieles gruesas como Cabernet)
4. Trasiego del jugo dejando pieles en tanque (aireación + redistribución de nutrientes)
5. Si glucosa >> fructosa: Re-inocular con levadura nueva
6. Re-evaluación: Al día siguiente mediante lectura de Brix + cata

**Causa raíz (#1)**: Nutrientes insuficientes, temperatura inapropiada, mala sanitación

### 2. Temperatura Crítica (OUT OF RANGE)

**Límites absolutos validados**:
- **Tintos**: 75°F - 90°F (23.9°C - 32.2°C)
- **Blancos**: 53°F - 62°F (11.7°C - 16.7°C)
- **Rosados**: 53°F - 62°F (11.7°C - 16.7°C)

**Trigger crítico**:
- Cambios repentinos de 10°F (5.6°C) en 2-4 horas = CRÍTICO
- Puede causar fermentación estancada

**Corrección**:
- Descenso de 2-6°C gradualmente para frenar fermentación demasiado vigorosa
- Método: Sistema de enfriamiento, mantas refrigerantes
- No ajustar bruscamente (riesgo de shock de levaduras)

### 3. Acidez Volátil (VOLATILE ACIDITY - Acetic Acid)

**Umbrales validados**:
- **En fruta (recepción)**: > 0.1 g/L = requiere atención
- **En vino - Blancos crítico**: > 0.5 g/L
- **En vino - Tintos crítico**: > 0.75 g/L
- **Alerta temprana**: 0.5 g/L (antes del crítico)

**Medición**:
- Método: Enzimático (destilación o kit enzimático)
- Frecuencia: Fruta (recepción), mid-fermentation, end-fermentation, vino (1x/mes)

**Detección temprana** (signos antes de medir):
- Visuales: Fruta podrida, con moho, con moscas de fruta
- Olfativas: Olor a vinagre durante fermentación lenta
- Gustativos: Cata diaria del jugo

### 4. Caída de Densidad Demasiado Rápida (DENSITY DROP TOO FAST)

**Umbral**: Caída > 15% en 24 horas

**Etapa más problemática**: Al comienzo de la fermentación

**Consecuencias**: 
- Vinos simples, poco aromáticos, sin complejidad
- Resultado de temperatura muy alta o demasiados nutrientes

**Acción correctiva**:
- Bajar temperatura 2-6°C para desacelerar fermentación
- Objetivo: Fermentación gradual = aromas y complejidad

### 5. Riesgo de Sulfuro de Hidrógeno (H₂S - "Rotten Egg")

**Condición favorecida**:
- Nutrientes nitrogenados insuficientes

**Detección**:
- Método: Cata diaria durante fermentación (olfativo - olor a huevo podrido)
- Tiras reactivas (si están disponibles)

**Protocolo preventivo**:
- Al inocular: Calcular requerimiento de nitrógeno (YAN) que la levadura demanda
- Asegurar nutrientes suficientes desde el inicio

**Si ya detectado H₂S**:
1. Si Brix > 5: Pequeña adición de nutrientes + aireación
2. Como último recurso: Adición de cobre (última opción)

### 6. Frecuencias Observadas (Prevalencia en LangeTwins)

- Fermentación estancada: **1%** de fermentaciones
- Temperatura fuera de rango crítico: **5%**
- Acidez volátil alta: **0.5%**
- Caída de densidad demasiado rápida: **10%**
- Problemas de H₂S: **0.5%**
- Temperatura subóptima (aceptable pero no ideal): **1%**
- **Intervención requerida**: ~**15%** de fermentaciones anuales

### 7. Ranking de Gravedad (1=MÁS GRAVE)

1. 🔴 **Acidez Volátil Alta** - Vino no vendible
2. 🔴 **Fermentación Estancada** - Lote puede perderse
3. 🟠 **Temperatura Fuera de Rango Crítico** - Daño severo
4. 🟠 **Duración Inusual** - Indicador de problemas
5. 🟡 **Caída de Densidad Demasiado Rápida** - Afecta calidad
6. 🟡 **H₂S** - Difícil de remediar
7. 🟡 **Patrón Atípico** - Early warning
8. ⚪ **Temperatura Subóptima** - Afecta aromas, reparable

### 8. Confianza en el Sistema

**Decisión sobre alertas**:
- Temperatura crítica: Investigaría inmediatamente si sistema lo alerta
- Falsos negativos vs falsos positivos: **Falsos negativos MÁS graves** (perder lotes)
- Recomendación de nutrientes: Verifica manualmente primero, luego ejecuta

**Datos históricos mínimos para confiar**:
- Mínimo: **5 fermentaciones** similares
- Ideal: **10 fermentaciones** similares
- Confianza crece: 15-30 (ALTA), >30 (MUY ALTA)

**Decisiones siempre humanas**:
1. Cómo limpiar jugos cuando hay H₂S presente
2. [Otros contextos específicos de dominio]

---

## Decision

### Architecture Overview

Módulo **Analysis Engine** con 4 capas:

```
analysis-engine/
├── domain/                    # Entities, Value Objects, Enums
│   ├── entities/
│   │   ├── analysis.py        # Aggregate Root
│   │   ├── anomaly.py
│   │   ├── recommendation.py
│   │   └── recommendation_template.py
│   ├── value_objects/
│   │   ├── comparison_result.py
│   │   ├── deviation_score.py
│   │   └── confidence_level.py
│   ├── enums/
│   │   ├── anomaly_type.py
│   │   ├── severity_level.py
│   │   ├── analysis_status.py
│   │   └── recommendation_category.py
│   └── repositories/          # Interfaces
│       ├── analysis_repository_interface.py
│       ├── anomaly_repository_interface.py
│       ├── recommendation_repository_interface.py
│       └── recommendation_template_repository_interface.py
│
├── repository_component/      # Persistence Implementation
│   └── repositories/
│       ├── analysis_repository.py
│       ├── anomaly_repository.py
│       ├── recommendation_repository.py
│       └── recommendation_template_repository.py
│
├── service_component/         # Business Logic
│   ├── interfaces/
│   │   ├── analysis_orchestrator_service_interface.py
│   │   ├── comparison_service_interface.py
│   │   ├── anomaly_detection_service_interface.py
│   │   ├── recommendation_service_interface.py
│   │   ├── rule_config_service_interface.py
│   │   └── cache_provider_interface.py
│   └── services/
│       ├── analysis_orchestrator_service.py
│       ├── comparison_service.py
│       ├── anomaly_detection_service.py
│       ├── recommendation_service.py
│       ├── rule_config_service.py
│       ├── in_memory_cache_provider.py
│       └── redis_cache_provider.py (future)
│
└── api_component/             # REST Endpoints
    ├── routers/
    │   └── analysis_router.py
    └── schemas/
        ├── requests.py
        └── responses.py
```

---

### Domain Layer Decisions

#### **Entities**

**1. Analysis** (Aggregate Root)
```python
id: int (PK)
fermentation_id: int (FK)
winery_id: int (multi-tenancy)
analyzed_at: datetime
analysis_status: AnalysisStatus
comparison_result: ComparisonResult (JSON)
confidence_level: ConfidenceLevel
historical_samples_count: int
execution_time_ms: int
# Relaciones:
anomalies: List[Anomaly] (1:N cascade)
recommendations: List[Recommendation] (1:N cascade)
```

**2. Anomaly**
```python
id: int (PK)
analysis_id: int (FK)
anomaly_type: AnomalyType
severity: SeverityLevel
detected_at: datetime
sample_id: Optional[int] (FK)
deviation_score: DeviationScore (JSON)
description: str (auto-generated)
is_resolved: bool
resolved_at: Optional[datetime]
```

**3. Recommendation**
```python
id: int (PK)
analysis_id: int (FK)
anomaly_id: int (FK)
recommendation_template_id: int (FK)
recommendation_text: str (personalized)
priority: int (1-5)
confidence: ConfidenceLevel
supporting_evidence_count: int
is_applied: bool
applied_at: Optional[datetime]
```

**4. RecommendationTemplate**
```python
id: int (PK)
code: str (UNIQUE) # REC_001_ADD_NUTRIENTS
title: str
description: str
category: RecommendationCategory
applicable_anomaly_types: List[AnomalyType] (JSON)
priority_default: int
is_active: bool
```

#### **Value Objects**

**ComparisonResult** (embebido en Analysis como JSON):
```python
avg_density_historical: float
current_density: float
deviation_percentage: float
percentile: int (0-100)
similar_fermentations_count: int
```

**DeviationScore** (embebido en Anomaly como JSON):
```python
z_score: Optional[float]  # Si hay datos suficientes
absolute_deviation: float
percentile_rank: Optional[int]
threshold_exceeded: bool
```

**ConfidenceLevel** (enum-like):
```python
LOW = <5 fermentations
MEDIUM = 5-15 fermentations
HIGH = 15-30 fermentations
VERY_HIGH = >30 fermentations
```

#### **Enums**

**AnomalyType** (8 tipos, basado en research):
```python
# Priority 1 - CRITICAL
STUCK_FERMENTATION
TEMPERATURE_OUT_OF_RANGE_CRITICAL
VOLATILE_ACIDITY_HIGH

# Priority 2 - WARNING
DENSITY_DROP_TOO_FAST
HYDROGEN_SULFIDE_RISK
TEMPERATURE_SUBOPTIMAL

# Priority 3 - INFO
UNUSUAL_DURATION
ATYPICAL_PATTERN
```

**SeverityLevel**:
```python
INFO = "INFO"
WARNING = "WARNING"
CRITICAL = "CRITICAL"
```

---

### Service Layer Decisions

#### **1. AnalysisOrchestratorService** (Coordinator)
**Responsabilidad**: Coordinar flujo end-to-end

**Flow**:
1. Validar fermentation existe (multi-tenancy check)
2. Obtener patrones históricos (PatternAnalysisService - ADR-034)
3. Comparar actual vs históricos (ComparisonService)
4. Detectar anomalías (AnomalyDetectionService)
5. Generar recomendaciones (RecommendationService)
6. Persistir Analysis + hijos (transacción)
7. Retornar Analysis completo

#### **2. ComparisonService** (Statistical Comparison)
**Responsabilidad**: Comparar fermentation actual vs patrones históricos

**Algoritmo**:
- Calcular promedios actuales (density, sugar, duration)
- Comparar con promedios históricos
- Calcular desviaciones (absolute, percentage, z-score)
- Determinar percentile ranking
- Calcular confidence level (basado en sample count)

**Caché Strategy**:
```python
# Interface (permite swap in-memory → Redis)
class ICacheProvider(ABC):
    async def get(key: str) -> Optional[Any]
    async def set(key: str, value: Any, ttl_seconds: int) -> None
    async def delete(key: str) -> None
    async def clear_pattern(pattern: str) -> None

# MVP Implementation
class InMemoryCacheProvider(ICacheProvider):
    # dict con {key: (value, expiration_timestamp)}

# Future Implementation (sin cambiar lógica)
class RedisCacheProvider(ICacheProvider):
    # redis.asyncio client
```

**Cache Keys & TTL**:
```
pattern:winery_{winery_id}:fruit_origin_{origin_id}  # TTL: 30min
comparison:fermentation_{fermentation_id}  # TTL: 5min
```

#### **3. AnomalyDetectionService** (Hybrid Algorithm)
**Responsabilidad**: Detectar anomalías usando algoritmos híbridos

**Algoritmo Híbrido**:
```python
async def detect_anomalies(...) -> List[Anomaly]:
    anomalies = []
    
    # 1. SIEMPRE aplicar reglas basadas en YAML
    rule_based = await self._apply_rules(fermentation, rules_config)
    anomalies.extend(rule_based)
    
    # 2. SOLO si hay datos suficientes (≥10), aplicar estadístico
    if comparison_result.similar_fermentations_count >= 10:
        statistical = await self._detect_statistical(comparison_result)
        anomalies.extend(statistical)
    
    # 3. Deduplicar (misma anomaly + sample)
    deduplicated = self._deduplicate(anomalies)
    
    # 4. Enriquecer (severity, description)
    enriched = self._enrich_anomalies(deduplicated, fermentation)
    
    return enriched
```

**Rule-Based Detection** (YAML-driven):
```yaml
# config/anomaly_rules.yaml
anomaly_rules:
  - name: STUCK_FERMENTATION
    severity: CRITICAL
    conditions:
      - type: density_change
        operator: less_than
        threshold: 2.0  # points
        timeframe_days: 3
    recommendations:
      - template_code: REC_001_ADD_NUTRIENTS
      - template_code: REC_002_INCREASE_TEMP
      - template_code: REC_003_ADD_STARTER

  - name: TEMPERATURE_OUT_OF_RANGE_CRITICAL
    severity: CRITICAL
    conditions:
      - type: temperature
        operator: less_than
        threshold: 15.0
      - type: temperature
        operator: greater_than
        threshold: 32.0
    recommendations:
      - template_code: REC_010_ADJUST_TEMPERATURE_URGENT
```

**Statistical Detection** (Z-score, Percentiles):
```python
# Si z_score > 3.0 → CRITICAL
# Si z_score > 2.0 → WARNING
# Si z_score > 1.5 → INFO
# Percentile: si está en top 5% o bottom 5% → anomaly
```

**Fallback**: Si no hay datos históricos (nueva winery), solo aplicar reglas básicas.

#### **4. RecommendationService** (Template-Based)
**Responsabilidad**: Generar recomendaciones basadas en templates pre-cargados

**Algoritmo**:
```python
async def generate_recommendations(anomalies, fermentation) -> List[Recommendation]:
    recommendations = []
    
    for anomaly in anomalies:
        # 1. Obtener templates aplicables
        templates = await repo.get_by_anomaly_type(anomaly.anomaly_type)
        
        # 2. Rankear por efectividad histórica (MVP: usar priority_default)
        ranked = await self._rank_by_effectiveness(templates, fermentation)
        
        # 3. Crear top 3-5 recomendaciones
        for template in ranked[:5]:
            rec = Recommendation(
                recommendation_text=self._personalize(template, anomaly),
                priority=self._calculate_priority(anomaly.severity, template),
                confidence=self._calculate_confidence(template, fermentation),
                supporting_evidence_count=self._count_similar_cases(...)
            )
            recommendations.append(rec)
    
    return recommendations
```

**Template Personalization** (placeholders):
```python
# Template: "Reducir temperatura a {target_temp}°C en {timeframe} horas"
# Personalized: "Reducir temperatura a 20°C en 6-8 horas"
```

**Effectiveness Ranking** (future enhancement):
- **MVP**: Ordenar por `priority_default` del template
- **Future**: Integrar con Action Tracking Module (ADR-022)
  - Query: ¿Cuántas veces se aplicó este template con éxito?
  - ML: Predecir probabilidad de éxito basado en contexto

#### **5. RuleConfigService** (YAML Loader)
**Responsabilidad**: Cargar y validar reglas desde archivo YAML

**Features**:
- Validación de estructura YAML (Pydantic models)
- Caché en memoria (performance)
- Hot-reload en desarrollo (production: restart required)
- Fail-fast si YAML inválido (startup check)

---

### API Layer Decisions

#### **Endpoints Design**

**Command Endpoints** (POST/PATCH - side effects):
- `POST /api/v1/fermentations/{id}/analyze` → Ejecutar análisis
- `PATCH /api/v1/anomalies/{id}/resolve` → Marcar anomaly resuelta
- `PATCH /api/v1/recommendations/{id}/apply` → Marcar recommendation aplicada

**Query Endpoints** (GET - read-only):
- `GET /api/v1/fermentations/{id}/analyses` → Listar análisis históricos
- `GET /api/v1/fermentations/{id}/analyses/latest` → Último análisis completo
- `GET /api/v1/analyses/{id}` → Análisis específico con hijos
- `GET /api/v1/analyses/{id}/anomalies` → Solo anomalías
- `GET /api/v1/analyses/{id}/recommendations` → Solo recomendaciones

#### **Authorization & Multi-Tenancy**
- JWT authentication (shared auth module - ADR-007)
- winery_id filtering (ADR-025)
- Ownership validation: user can only access own fermentations

#### **Performance Targets**
- Análisis completo: < 2 segundos (incluye I/O)
- List endpoints: Pagination mandatory (max 50 items)
- Eager loading: anomalies + recommendations en detail endpoints (avoid N+1)

---

## Consequences

### Positive Consequences

✅ **High Business Value**: Core differentiator del sistema (CRUD → Intelligent Assistant)

✅ **Data-Driven Decisions**: Winemakers tienen recomendaciones basadas en históricos reales

✅ **Scalable Algorithm**: Híbrido (rules + statistical) funciona con pocas o muchas fermentaciones

✅ **Maintainability**: 
- Reglas configurables (YAML) → ajustar sin redeploy
- Templates en DB → fácil agregar/modificar recomendaciones
- Interface-based cache → migrar a Redis sin cambiar lógica

✅ **Extensibility**:
- Fácil agregar nuevos AnomalyType (solo actualizar enum + YAML)
- Ranking de recomendaciones mejora con Action Tracking data (future)
- Algoritmos estadísticos más avanzados (ML) son plug-and-play

✅ **Performance**: 
- Caché de patrones históricos (30min TTL)
- Async/await para I/O bound operations
- Target < 2 segundos alcanzable

✅ **User Experience**:
- On-demand analysis (Fase 1 MVP)
- Event-driven automático (Fase 2) - desbloquea flujo pasivo
- Confidence levels comunican certeza al usuario

---

### Negative Consequences / Trade-offs

⚠️ **Complejidad Algorítmica**: Híbrido (rules + statistical) aumenta surface area de bugs

**Mitigation**: Tests exhaustivos (unit + integration), validación con domain expert

⚠️ **Dependencia de Datos Históricos**: Sistema es menos útil en primeras fermentaciones

**Mitigation**: Fallback a rules básicas, mostrar confidence LOW, UI warning

⚠️ **Mantenimiento de Reglas YAML**: Requiere validación cuidadosa, riesgo de typos

**Mitigation**: Pydantic validation, startup checks, tests de reglas específicas

⚠️ **Cache Coherence**: In-memory cache no se sincroniza entre instancias (single-instance solo)

**Mitigation**: MVP es single-instance, migrar a Redis cuando escale a multi-instance

⚠️ **Seed Data Requirement**: Templates deben pre-cargarse, mantener seed script actualizado

**Mitigation**: Seed script versionado en git, documentation de templates

⚠️ **False Positives Risk**: Z-score puede disparar alertas en casos normales (variedad específica)

**Mitigation**: Confidence levels, filtrado por fruit_origin, threshold configurable en YAML

---

### Risks and Mitigations

**Risk 1: Algoritmo genera demasiados false positives (alert fatigue)**
- **Probability**: Medium
- **Impact**: High (usuarios ignoran alertas)
- **Mitigation**: 
  - Empezar con thresholds conservadores (Z-score > 3.0 para CRITICAL)
  - Monitorear feedback de winemakers
  - Ajustar thresholds en YAML basándonos en data real

**Risk 2: Performance < 2 segundos con muchos samples**
- **Probability**: Low (queries optimizados, caché)
- **Impact**: Medium (UX degraded)
- **Mitigation**: 
  - Profiling temprano en desarrollo
  - Index en campos críticos (fermentation_id, analyzed_at)
  - Pagination en queries de samples

**Risk 3: Primeras wineries sin datos históricos tienen mala experiencia**
- **Probability**: High (inevitable en onboarding)
- **Impact**: Medium (expectativas no cumplidas)
- **Mitigation**:
  - UI/UX comunicar claramente confidence LOW
  - Tooltips explicando necesidad de datos históricos
  - Considerar Phase 3: datos agregados de otras wineries (anonimizados)

**Risk 4: YAML mal configurado en producción rompe análisis**
- **Probability**: Low (startup validation)
- **Impact**: Critical (análisis no funciona)
- **Mitigation**:
  - Validation exhaustiva en startup (fail-fast)
  - YAML versionado en git (code review)
  - Tests de reglas específicas (unit tests)

---

## Implementation Plan

### Phase 1: Domain + Repository (3 días)

**Week 1 - Days 1-3**

**Tasks**:
- [ ] Crear enums (`AnomalyType`, `SeverityLevel`, `AnalysisStatus`, `RecommendationCategory`)
- [ ] Crear value objects (`ComparisonResult`, `DeviationScore`, `ConfidenceLevel`)
- [ ] Crear entities (`Analysis`, `Anomaly`, `Recommendation`, `RecommendationTemplate`)
- [ ] Crear repository interfaces
- [ ] Implementar repositories con SQLAlchemy
- [ ] Crear migration scripts (Alembic)
- [ ] **Tests**: 30 unit tests (value objects + entities), 20 integration tests (repositories)

**Deliverables**:
- `src/modules/analysis-engine/src/domain/` completo
- `src/modules/analysis-engine/src/repository_component/` completo
- DB migrations funcionando
- 50 tests passing

---

### Phase 2: Service Layer Core (4 días)

**Week 1 Day 4 - Week 2 Day 2**

**Tasks**:
- [ ] Implementar `ICacheProvider` + `InMemoryCacheProvider`
- [ ] Implementar `RuleConfigService` + validación YAML
- [ ] Crear `config/anomaly_rules.yaml` con 8 reglas (research-based)
- [ ] Implementar `ComparisonService` (algoritmo comparación + caché)
- [ ] Implementar `AnomalyDetectionService` (híbrido: rules + statistical)
- [ ] Implementar `RecommendationService` (template-based)
- [ ] **Tests**: 40 unit tests (mocks), 15 integration tests (DB real)

**Deliverables**:
- `anomaly_rules.yaml` versionado
- Services funcionando en aislamiento
- 55 tests passing

---

### Phase 3: Orchestration + API (3 días)

**Week 2 Days 3-5**

**Tasks**:
- [ ] Implementar `AnalysisOrchestratorService` (coordina todo)
- [ ] Implementar API router con 8 endpoints
- [ ] Crear Pydantic schemas (requests + responses)
- [ ] Integrar error handling (ADR-008)
- [ ] Implementar dependency injection
- [ ] **Tests**: 20 unit tests (orchestrator), 15 API tests (TestClient)

**Deliverables**:
- API completa funcionando
- OpenAPI docs (/docs)
- 35 tests passing

---

### Phase 4: Seed Data + Integration Testing (2 días)

**Week 2 Days 6-7**

**Tasks**:
- [ ] Crear seed script para `recommendation_templates` (20-30 templates)
- [ ] Poblar templates basados en research + domain expertise
- [ ] Tests de integración end-to-end (POST /analyze → GET /analyses)
- [ ] Performance testing (medir tiempo de análisis)
- [ ] Documentation (actualizar ADR-INDEX, module-context)
- [ ] **Tests**: 10 E2E tests, performance benchmarks

**Deliverables**:
- Seed script funcional (`scripts/seed_recommendation_templates.py`)
- Performance < 2 segundos validado
- 10 E2E tests passing

---

### Phase 5: Documentation + Deployment (1 día)

**Week 3 Day 1**

**Tasks**:
- [ ] Actualizar ADR-PENDING-GUIDE (mark ADR-020 complete)
- [ ] Actualizar ADR-INDEX
- [ ] Crear README del módulo
- [ ] Deployment a staging
- [ ] Smoke tests en staging

**Deliverables**:
- ADR-020 marcado como ✅ Implemented
- Módulo deployado y funcional

---

### Summary
- **Total Duration**: 12-13 días (~2.5 semanas)
- **Total Tests**: ~150 tests (87% coverage target maintained)
- **Test Breakdown**:
  - Unit tests: ~90 (domain + service layer mocked)
  - Integration tests: ~50 (DB real, service coordination)
  - API tests: ~15 (FastAPI TestClient)
  - E2E tests: ~10 (flujo completo)
- **Dependencies**: Ninguna (prerequisites ya completos)

---

## Open Questions / Future Enhancements

**📋 Status Update (Jan 16, 2026):**
- User confirmed threshold questions will be sent to enologist for expert validation
- Created comprehensive questionnaire: `src/modules/analysis-engine/.ai-context/preguntas-enologo.md` (8 sections, 70+ questions)
- Questionnaire covers: thresholds, remediation protocols, anomaly frequencies, impact ranking, practical context
- Scientific research (Wikipedia, MDPI, Frontiers in Microbiology) confirmed phenomena but lacks operational thresholds
- **Next step:** User sends questionnaire to enologist, awaits responses before implementation

### Resolved Questions ✅

**Q1: ¿Incluir varietal en similarity matching?** ✅ RESOLVED
- **User Decision (3.c):** "la prioridad es la misma variedad y despues el fruit origin"
- **Priority Order**: VARIETAL (Priority 1) → fruit_origin (Priority 2) → fermentation_type (Priority 3) → initial_density (Priority 4)
- **Rationale**: Varietal characteristics (phenolics, sugar levels, fermentation kinetics) are more deterministic than terroir for fermentation patterns
- **Implementation**: Query `harvest_lot.varietal_mix` or `fruit_origin.varietal` as first filter

**Q2: ¿Mostrar confidence level al winemaker?** ✅ RESOLVED
- **User Clarification (2.f):** "es q no entiendo el sistema tiene q ser lo mas fiable posible o te refieres cuando sabemos q es confiable?"
- **Decision**: ALWAYS show confidence level with visual indicators - reliability comes from transparency, not hiding uncertainty
- **Implementation**:
  - LOW (<5): ⚠️ Yellow warning, "Limited historical data - use with caution"
  - MEDIUM (5-15): ℹ️ Blue info, "Moderate historical data"
  - HIGH (15-30): ✅ Green check, "Strong historical data"
  - VERY_HIGH (>30): ✅✅ Green double-check, "Very strong historical data"
  - Include sample count tooltip: "Based on 23 similar fermentations"
- **Rationale**: Professional users (enologists) need to know data limitations to make informed decisions

### To Resolve Before Implementation (Priority 1)

**Q1: Numerical Thresholds Validation** ⏳ Awaiting Enologist Input
- **Question**: Are the proposed thresholds scientifically sound for production winery operations?
- **Status**: User will send questionnaire to enologist (see `preguntas-enologo.md` Section 1)
- **Current Estimates** (Conservative - Subject to Expert Validation):
  - Stuck fermentation: 3 days + <2 points density change
  - Temperature critical: <15°C or >32°C
  - Density drop fast: >15% in 24 hours
- **Action Required**: Await enologist responses, update YAML rules accordingly

**Q2: Top 3 Critical Anomalies** ⏳ Awaiting Enologist Input
- **Question**: Based on real-world experience, which 3 anomalies are MOST FREQUENT and MOST DAMAGING?
- **Status**: User will send questionnaire to enologist (see `preguntas-enologo.md` Section 5.1, 6.1)
- **Purpose**: Prioritize implementation resources and testing for highest-impact detections
- **Action Required**: Enologist ranking of 8 anomaly types by severity and frequency

**Q3: Initial Recommendation Templates** ⏳ Awaiting Enologist Input
- **Question**: What are the standard remediation protocols for top anomalies?
- **Status**: User will send questionnaire to enologist (see `preguntas-enologo.md` Section 3)
- **Examples Needed**:
  - Stuck fermentation: Nutrient type, quantity (g/hL), re-inoculation protocol
  - Temperature adjustments: Gradual vs immediate, target ranges
  - H₂S prevention: Preventive nutrients, reactive measures
- **Action Required**: 5-10 validated recommendation texts for seed script

**Q4: Varietal Filtering Implementation** ⏳ Data Verification Needed
- **Question Resolved**: Priority confirmed (Varietal #1 → fruit_origin #2)
- **Question Remaining**: Is varietal data available in `harvest_lot.varietal_mix` or `fruit_origin.varietal`?
- **Action Required**: Query database schema, verify data availability
- **Fallback**: If not available in MVP, implement fruit_origin-only comparison

**Q5: ¿Cómo manejar anomalías recurrentes?**
- **Escenario**: STUCK_FERMENTATION detectado 3 días seguidos
- **Opciones**:
  - A) 3 Anomaly entities separadas (más simple)
  - B) 1 Anomaly con `occurrences_count` (más compacto)
- **Decisión pendiente**: Validar con UX mockups

**Q6: ¿Threshold de historical_samples_count para estadístico?**
- **Propuesta actual**: ≥10 para aplicar Z-score
- **Pregunta**: ¿Es suficiente? ¿Muy bajo?
- **Acción**: Consultar con data scientist / statistician

---

### Future Ideas (Post-MVP) 🔓

**Recommendation Template Evolution** (Q3.b - User: "no tengo mas ideas pero dejemos esto abierto")
- Track `is_applied` and subsequent fermentation success
- Build effectiveness rankings: "When X was applied for stuck fermentation, success rate: 85%"
- User feedback: "This recommendation was helpful/not helpful" (boolean + optional comment)
- Template versioning: Track changes over time
- ML-based recommendation: Suggest templates based on historical success patterns
- A/B testing: Compare effectiveness of different remediation protocols
- **Decision**: Implement basic tracking now, evolve algorithm as we gather data and new ideas emerge

---

### Phase 2 Enhancements (Post-MVP)

**Enhancement 1: Event-Driven Analysis** (ADR-021 dependency)
- Trigger automático cuando se agrega nuevo sample
- Requiere: Event bus (Celery, RabbitMQ, o AWS EventBridge)
- Benefit: UX pasivo (no requiere click "Analyze")

**Enhancement 2: Redis Cache** (scalability)
- Migrar de in-memory a Redis (preparado con `ICacheProvider`)
- Benefit: Multi-instance support, cache distribuido
- Requiere: Redis deployment + configuration

**Enhancement 3: ML-Based Recommendation Ranking** (ADR-022 dependency)
- Integrar con Action Tracking Module
- Ranking dinámico basado en efectividad histórica
- Benefit: Recomendaciones mejoran con el tiempo

**Enhancement 4: Varietal-Specific Rules** (advanced)
- YAML rules con filtros por varietal
- Ejemplo: Malbec tiene thresholds diferentes que Pinot Noir
- Benefit: Mayor precisión, menos false positives

**Enhancement 5: Exportar análisis a PDF/Excel**
- Endpoint: `GET /analyses/{id}/export?format=pdf`
- Requiere: reportlab o similar
- Benefit: Reportes impresos para auditoría

---

## Alternatives Considered

### Alternative 1: ML-Only (No Rules)
**Descripción**: Usar solo machine learning (regresión, clasificación) sin reglas hardcoded

**Pros**:
- Más "inteligente" (aprende de data)
- Potencialmente más preciso con suficiente training data

**Cons**:
- ❌ Requiere training data (no disponible en MVP)
- ❌ Black box (difícil explicar al usuario por qué se detectó anomaly)
- ❌ Más complejo implementar y mantener

**Rejected**: No hay training data suficiente, necesidad de bootstrap inmediato

---

### Alternative 2: Rules-Only (No Statistical)
**Descripción**: Solo reglas basadas en YAML, sin análisis estadístico

**Pros**:
- ✅ Más simple de implementar
- ✅ Más fácil de entender y debuggear
- ✅ No requiere datos históricos

**Cons**:
- ❌ No aprovecha patrones históricos (desaprovecha valor de Historical Data)
- ❌ Thresholds fijos pueden no ser óptimos para todas las wineries
- ❌ No detecta "ATYPICAL_PATTERN" (desviación sutil del promedio)

**Rejected**: Desaprovecha valor de datos históricos, no es "inteligente"

---

### Alternative 3: No Persistir Análisis (On-Demand Only)
**Descripción**: Calcular análisis on-the-fly, no guardar en DB

**Pros**:
- ✅ Más simple (no repository layer)
- ✅ Siempre actualizado (no stale data)

**Cons**:
- ❌ No hay tracking histórico ("¿qué anomalías detectamos hace 2 meses?")
- ❌ No se puede analizar accuracy de predicciones
- ❌ Performance: recalcular cada vez es más lento

**Rejected**: Usuario especificó necesidad de guardar (tracking + mejora continua)

---

### Alternative 4: Templates en YAML (no DB)
**Descripción**: Guardar templates en archivo YAML junto con rules

**Pros**:
- ✅ Versionado en git
- ✅ Code review de cambios
- ✅ Más simple deployment

**Cons**:
- ❌ Difícil agregar templates largos (párrafos de texto)
- ❌ No permite UI admin en futuro
- ❌ Más difícil localización (i18n)

**Rejected**: Templates requieren flexibilidad y UI admin futura

---

## References

### Research Sources
- **Wikipedia**: "Fermentation in Winemaking" (accessed January 16, 2026)
- **Jancis Robinson**: "The Oxford Companion to Wine" (3rd Edition)
- **Domain Expertise**: Input de winemaker (usuario del sistema)

### Related ADRs
- [ADR-034](./ADR-034-historical-data-service-refactoring.md): PatternAnalysisService (prerequisite)
- [ADR-032](./ADR-032-historical-data-api-layer.md): Historical Data API
- [ADR-027](./ADR-027-structured-logging-observability.md): Logging infrastructure
- [ADR-025](./ADR-025-multi-tenancy-security-light.md): Multi-tenancy
- [ADR-008](./ADR-008-centralized-error-handling.md): Error handling pattern
- [ADR-007](./ADR-007-auth-module-design.md): Authentication

### Future ADRs
- **ADR-021**: Alerting & Notification Strategy (depends on ADR-020)
- **ADR-022**: Action Tracking Module (depends on ADR-021)

---

## Approval

**Status**: 🔄 In Progress - Pending review & implementation  
**Stakeholders to Review**:
- ✅ Development Team (architecture documented)
- ⏳ Domain Expert (validate anomaly priorities + recommendations)
- ⏳ UX Designer (validate confidence level display)

**Next Steps**:
1. Review open questions with stakeholders
2. Validate anomaly priorities con domain expert
3. Start Phase 1 implementation (Domain + Repository)

---

**Última actualización**: January 16, 2026  
**Versión**: 1.0.0

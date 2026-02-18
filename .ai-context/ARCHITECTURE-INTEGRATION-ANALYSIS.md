# Análisis de Integración: Protocolos + Analysis Engine (ADR-021 + ADR-020)

**Fecha**: Febrero 6, 2026  
**Nivel**: Arquitectura (Sin código)  
**Scope**: Dónde van los protocolos + Integración con Analysis Engine + MVP vs Futuro

---

## 📊 ARQUITECTURA ACTUAL (Sistema Completo)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        WINE FERMENTATION SYSTEM                     │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  WINERY      │  │  FRUIT       │  │ FERMENTATION│              │
│  │  MODULE      │  │  ORIGIN      │  │ MODULE      │              │
│  │              │  │  MODULE      │  │             │              │
│  │ ✅ Complete  │  │ ✅ Complete  │  │ ✅ Complete │              │
│  │              │  │              │  │             │              │
│  │ • Winery CRUD│  │ • Vineyard   │  │ • Ferment   │              │
│  │ • Services   │  │ • Harvest    │  │   CRUD      │              │
│  │ • API Layer  │  │ • Services   │  │ • Sample    │              │
│  │              │  │ • API        │  │   CRUD      │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│         ↓                  ↓                  ↓                      │
│  ┌─────────────────────────────────────────────────────┐            │
│  │              SHARED INFRASTRUCTURE                  │            │
│  ├─────────────────────────────────────────────────────┤            │
│  │ • Authentication Module (JWT, Multi-tenancy)       │            │
│  │ • Error Handling (Centralized)                      │            │
│  │ • Structured Logging (Loguru + Structlog)           │            │
│  │ • Testing Infrastructure (Fixtures, Base Configs)   │            │
│  │ • Database (PostgreSQL, SQLAlchemy ORM)             │            │
│  └─────────────────────────────────────────────────────┘            │
│         ↑                                     ↑                       │
│  ┌──────────────────────────────────────────────────────┐            │
│  │        HISTORICAL DATA MODULE                        │            │
│  ├──────────────────────────────────────────────────────┤            │
│  │ ✅ Phase 1 COMPLETE (Domain + Repository)            │            │
│  │                                                      │            │
│  │ • ETL Pipeline (Importa Excel histórico)            │            │
│  │ • Pattern Extraction Service                        │            │
│  │ • Data Source Tracking (ADR-029)                     │            │
│  │ • Historical API Layer (Query, Compare)              │            │
│  └──────────────────────────────────────────────────────┘            │
│         ↑                                     ↑                       │
│  ┌──────────────────────────────────────────────────────┐            │
│  │     ANALYSIS ENGINE MODULE (ADR-020)                 │            │
│  ├──────────────────────────────────────────────────────┤            │
│  │ 🔄 Phase 1 COMPLETE (Domain + Repository)            │            │
│  │                                                      │            │
│  │ • RecommendationRepository (9 methods)              │            │
│  │ • RecommendationTemplateRepository (11 methods)     │            │
│  │ • Analysis, Anomaly, Recommendation Entities        │            │
│  │ • Anomaly Detection Algorithms                      │            │
│  │ • Recommendation Engine                            │            │
│  │                                                      │            │
│  │ ⏳ Phase 2-5 PENDING:                                │            │
│  │   • Service Layer                                   │            │
│  │   • API Endpoints                                   │            │
│  │   • Integration Tests                               │            │
│  └──────────────────────────────────────────────────────┘            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

CURRENT STATE: 1,158 tests passing (100%)
NEXT PHASE: Analysis Engine Services + Protocol Engine
```

---

## 🎯 DÓNDE VA ADR-021 (PROTOCOL ENGINE)

### **Opción 1: Módulo SEPARADO (Recomendado)**

```
ARCHITECTURE (NUEVO):

┌─────────────────────────────────────────────────────────────────────┐
│                    ANALYSIS ENGINE CONTEXT                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────┐  ┌─────────────────────────┐          │
│  │  PROTOCOL ENGINE        │  │  ANALYSIS ENGINE        │          │
│  │  (ADR-021)              │  │  (ADR-020)              │          │
│  ├─────────────────────────┤  ├─────────────────────────┤          │
│  │                         │  │                         │          │
│  │ Domain:                 │  │ Domain:                 │          │
│  │ • FermentationProtocol  │  │ • Analysis              │          │
│  │ • ProtocolStep          │  │ • Anomaly               │          │
│  │ • ProtocolExecution     │  │ • Recommendation        │          │
│  │ • ExecutedStep          │  │ • DeviationScore        │          │
│  │                         │  │                         │          │
│  │ Service:                │  │ Service:                │          │
│  │ • ProtocolService       │  │ • AnomalyDetection      │          │
│  │ • ComplianceService     │  │ • RecommendationEngine  │          │
│  │ • DeviationDetector     │  │ • AnalysisOrchestrator  │          │
│  │                         │  │                         │          │
│  │ API:                    │  │ API:                    │          │
│  │ • GET /protocols        │  │ • POST /analyze         │          │
│  │ • POST /execute-step    │  │ • GET /recommendations  │          │
│  │ • GET /compliance       │  │                         │          │
│  │                         │  │                         │          │
│  └─────────────────────────┘  └─────────────────────────┘          │
│           ↓                              ↓                          │
│  ┌───────────────────────────────────────────────────────┐          │
│  │     UNIFIED ANALYSIS SERVICE                          │          │
│  │     (Orquesta Protocol + Analysis)                   │          │
│  │                                                       │          │
│  │  Protocol + Analysis → Smart Decisions               │          │
│  └───────────────────────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Por qué módulo separado:**
- ✅ Separación de concerns clara
- ✅ Protocol Engine = Sistema operacional (recetas)
- ✅ Analysis Engine = Sistema inteligente (anomalías + recomendaciones)
- ✅ Ambos viven en `src/modules/analysis_engine/` (mismo bounded context)
- ✅ Fácil de testear independientemente

**Estructura física:**

```
src/modules/analysis_engine/
├── domain/
│   ├── entities/
│   │   ├── analysis.py
│   │   ├── anomaly.py
│   │   ├── recommendation.py
│   │   ├── fermentation_protocol.py          ← NUEVO (ADR-021)
│   │   ├── protocol_step.py                   ← NUEVO (ADR-021)
│   │   └── protocol_execution.py              ← NUEVO (ADR-021)
│   └── enums/
│       ├── anomaly_type.py                    (AMPLIADO)
│       └── protocol_deviation_type.py         ← NUEVO (ADR-021)
│
├── repository_component/
│   └── repositories/
│       ├── analysis_repository.py
│       ├── anomaly_repository.py
│       ├── recommendation_repository.py
│       ├── protocol_repository.py             ← NUEVO (ADR-021)
│       └── protocol_execution_repository.py   ← NUEVO (ADR-021)
│
├── service_component/
│   └── services/
│       ├── analysis_service.py                (existente)
│       ├── protocol_service.py                ← NUEVO (ADR-021)
│       ├── protocol_compliance_service.py     ← NUEVO (ADR-021)
│       └── unified_analysis_service.py        ← NUEVO (Orquesta ambos)
│
├── api_component/
│   ├── routers/
│   │   ├── analysis_router.py                 (existente)
│   │   └── protocol_router.py                 ← NUEVO (ADR-021)
│   └── schemas/
│       ├── analysis_schemas.py                (existente)
│       └── protocol_schemas.py                ← NUEVO (ADR-021)
│
└── tests/
    ├── unit/
    │   ├── services/
    │   │   ├── test_analysis_service.py
    │   │   ├── test_protocol_service.py       ← NUEVO
    │   │   └── test_protocol_compliance.py    ← NUEVO
    │   └── repositories/
    │       ├── test_analysis_repo.py
    │       ├── test_protocol_repo.py          ← NUEVO
    │       └── test_protocol_execution_repo.py ← NUEVO
    │
    └── integration/
        ├── modules/analysis_engine/
        │   ├── repositories/
        │   │   ├── test_analysis_repo_integration.py
        │   │   ├── test_protocol_repo_integration.py     ← NUEVO
        │   │   └── test_protocol_execution_integration.py ← NUEVO
        │   └── services/
        │       ├── test_analysis_service_integration.py
        │       ├── test_protocol_service_integration.py  ← NUEVO
        │       └── test_unified_analysis_integration.py  ← NUEVO
```

---

## 🔗 INTEGRACIÓN CON ANALYSIS ENGINE

### **Flujo Actual (Sin Protocolo)**

```
Fermentation Data
       ↓
┌─────────────────────┐
│ Analysis Service    │
│ (ADR-020)           │
├─────────────────────┤
│ • Load historical   │
│ • Calculate Z-score │
│ • Detect anomalies  │
│ • Generate recs     │
└─────────────────────┘
       ↓
"Brix drop is slow"
"Recommend: Add nutrients"
(Without context of what's expected)
```

### **Flujo Nuevo (Con Protocolo)**

```
Fermentation Data
       ↓
    ┌──┴──┐
    ↓     ↓
┌──────┐ ┌────────────┐
│ Ptcl │ │ Analysis   │
│ Eng  │ │ (ADR-020)  │
├──────┤ ├────────────┤
│What  │ │What's      │
│SHOULD│ │ACTUALLY    │
│happen│ │happening?  │
│      │ │            │
└──┬───┘ └────┬───────┘
   │          │
   └────┬─────┘
        ↓
┌───────────────────────────┐
│ Unified Analysis Service  │
│                          │
│ Expected vs Actual       │
│ ↓                        │
│ Deviation detected?      │
│ ↓                        │
│ Smart Action             │
│ (with protocol context)  │
└───────────────────────────┘
       ↓
"Brix drop 0.8/day (expected 1-2/day)"
"Status: Borderline (monitor 24h)"
"IF drops <0.5 tomorrow: Add KMBS + nutrients"
(With clear prescriptive action)
```

### **Especificaciones de Integración**

```
┌──────────────────────────────────────────────────────────┐
│ UNIFIED ANALYSIS SERVICE (New Orchestrator)              │
├──────────────────────────────────────────────────────────┤
│                                                          │
│ INPUT: fermentation_id                                  │
│                                                          │
│ 1. Get Protocol Execution                              │
│    └─ What steps should be done?                       │
│    └─ What's been done?                                │
│                                                          │
│ 2. Get Current Fermentation Data                       │
│    └─ Temperature, Brix, pH, etc.                      │
│                                                          │
│ 3. Call Analysis Service                               │
│    └─ Statistical analysis vs historical               │
│    └─ Detect anomalies (Z-score, percentiles)          │
│                                                          │
│ 4. Correlate with Protocol                             │
│    ├─ Is current state within expected range?          │
│    ├─ Should this step have been done by now?          │
│    └─ Was a critical step skipped?                     │
│                                                          │
│ 5. Elevation Logic                                     │
│    ├─ Protocol deviation + Analysis anomaly            │
│    │  = CRITICAL elevation                             │
│    ├─ Protocol OK + Analysis anomaly                   │
│    │  = Monitor (might be normal variance)             │
│    └─ Protocol deviation + Analysis OK                 │
│       = Warning (watch for delayed anomaly)            │
│                                                          │
│ 6. Generate Smart Recommendations                      │
│    ├─ From Analysis (historical patterns)              │
│    └─ From Protocol (prescribed actions)               │
│                                                          │
│ OUTPUT: UnifiedAnalysisResult                           │
│ ├─ analysis_status: GREEN/YELLOW/RED                   │
│ ├─ protocol_status: ON_TRACK/LATE/SKIPPED              │
│ ├─ anomalies: [...]                                    │
│ ├─ protocol_deviations: [...]                          │
│ ├─ recommendations: [...] (ranked by priority)         │
│ ├─ confidence: LOW/MEDIUM/HIGH/VERY_HIGH               │
│ └─ next_critical_step: "..."                           │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

---

## 📍 DÓNDE VISUALIZAR (Contextos)

### **Archivos de Contexto a ACTUALIZAR**

```
ACTUALIZAR (ADD ADR-021):
├─ .ai-context/
│  ├─ project-context.md
│  │  └─ ADD "Protocol Engine Module" en módulos
│  │     Status: 📋 Proposed (ADR-021)
│  │     Phase: 1 (Domain + Repository)
│  │     Tests: 40 expected
│  │
│  └─ ADR-INDEX.md
│     └─ ADD ADR-021 entry
│        Status: 📋 Proposed
│        Impact: High
│
└─ src/modules/analysis_engine/
   └─ .ai-context/module-context.md (CREAR)
      └─ Document:
         • Full module architecture
         • ADR-020 (Analysis Engine) status
         • ADR-021 (Protocol Engine) status
         • Integration between both
         • Database entities (both engines)
         • Services (both engines)
         • API endpoints (both engines)
         • Test coverage
```

### **Nuevo Archivo de Contexto (Crear)**

```
CREAR: src/modules/analysis_engine/.ai-context/module-context.md

Contenido:
1. Module responsibility
   - Analysis Engine: Real-time anomaly detection + recommendations
   - Protocol Engine: Operational workflow tracking + compliance

2. Components & Status
   ├─ Analysis Engine (ADR-020)
   │  └─ Phase 1: ✅ COMPLETE
   │  └─ Phase 2-5: ⏳ PENDING
   │
   └─ Protocol Engine (ADR-021)
      └─ Phase 1-5: 📋 PROPOSED

3. Data Models (Both Engines)
   - Analysis: Analysis, Anomaly, Recommendation, DeviationScore
   - Protocol: FermentationProtocol, ProtocolStep, ProtocolExecution, ExecutedStep

4. Services & Integration
   - How they work together
   - Unified Analysis Service orchestrates both
   - Elevation logic for anomalies + deviations

5. API Endpoints (Both Engines)
   - Analysis: /analyze, /recommendations
   - Protocol: /protocols, /execute-step, /compliance

6. Test Strategy
   - Unit tests per service
   - Integration tests for unified analysis
   - End-to-end tests for full workflow

7. Implementation Timeline
   - Phase 1-2: 3-4 weeks for both engines
   - Phase 3-5: 2-3 weeks for APIs
```

---

## 🚀 MVP vs FUTURO (ML Clarification)

### **MVP (Scope Actual - ADR-020 + ADR-021)**

```
CORE INTELLIGENT FEATURES:
├─ Real-time anomaly detection (statistical)
│  ├─ Z-score analysis
│  ├─ Percentile comparison
│  └─ Trend detection
│
├─ Protocol compliance tracking
│  ├─ Step execution logging
│  ├─ Tolerance checking
│  └─ Compliance %
│
├─ Smart recommendations
│  ├─ Template-based (pre-written)
│  ├─ Ranked by effectiveness from past batches
│  └─ Confidence levels based on historical samples
│
├─ Deviation detection
│  ├─ Protocol vs actual
│  ├─ Analysis vs expected
│  └─ Combined severity assessment
│
└─ Audit trail
   ├─ Full execution history
   ├─ Compliance reports
   └─ Intervention tracking
```

**Capacidad: SMART pero NO ML**
- Las recomendaciones son "retrieval-based" (templatos preescritos)
- Confidence levels = "# of similar historical cases"
- No hay entrenamiento de modelos

**Example**:
```
Recommendation: "Add 10-15ppm KMBS"
Confidence: VERY_HIGH (32 historical cases with stuck fermentation)
Success Rate: 85% (27 of 32 were resolved by this action)
```

### **FUTURO (Post-MVP) - Machine Learning Layer**

```
⏭️ PHASE 2 (Not MVP):

ADVANCED PREDICTIVE FEATURES:
├─ Anomaly Prediction (not just detection)
│  └─ "In 6 hours you'll have stuck fermentation (80% probability)"
│
├─ Optimization Models
│  ├─ "Optimal fermentation temperature for THIS fruit"
│  ├─ "Nutrient dosage based on initial conditions"
│  └─ "Predicted finish time with 85% accuracy"
│
├─ Protocol Learning
│  ├─ "Protocol v2 is 15% better than v1"
│  ├─ "These 3 steps can be skipped without impact"
│  └─ "New varietal: Use CS protocol with 10% adjustments"
│
├─ Causal Analysis
│  ├─ "What factor caused stuck fermentation?"
│  ├─ "Skipped secondary nutrients → 3x stuck risk"
│  └─ "Temperature >60F → 2x slow fermentation"
│
└─ Automated Protocol Optimization
   └─ "Based on 2025 results, here's 2026 protocol v2"
```

**Requisitos para ML Layer**:
- 100+ historical fermentations per varietal (need 2-3 years data)
- Consistent measurement frequency
- Labeled outcomes (quality scores correlating to actions)
- Feature engineering (extract patterns from fermentation curves)

**Timeline**: Post-MVP, Q3 2026 or later

---

## 📊 TABLA RESUMEN: MVP vs Futuro

| Capacidad | MVP (ADR-020 + ADR-021) | Futuro (ML) |
|---|---|---|
| **Detect anomalies** | ✅ YES (Statistical) | ✅ YES (Predictive) |
| **Recommend actions** | ✅ YES (Template-based) | ✅ YES (Learning-based) |
| **Track protocol compliance** | ✅ YES | ✅ YES (+ optimization) |
| **Compare fermentations** | ✅ YES (Historical) | ✅ YES (Predictive) |
| **Detect deviations** | ✅ YES (Actual vs Expected) | ✅ YES (Trend-based) |
| **Predict problems** | ⏭️ NO (Reactive) | ✅ YES (Proactive) |
| **Auto-optimize protocol** | ⏭️ NO (Manual) | ✅ YES (Data-driven) |
| **Causal analysis** | ⏭️ NO | ✅ YES |
| **Personalize by fruit** | ⏭️ NO (Varietal only) | ✅ YES (Micro-level) |

---

## 🎯 IMPLEMENTATION ROADMAP

### **Phase 1: Analysis Engine Services (ADR-020 Phase 2-5)**
**Timeline**: 2-3 weeks  
**What**: Service Layer + API + Integration Tests for existing domain  
**Where**: `src/modules/analysis_engine/service_component/` + `api_component/`  
**Impact**: Enables analysis queries

### **Phase 2: Protocol Engine Domain + Services (ADR-021 Phase 1-2)**
**Timeline**: 2-3 weeks  
**What**: Domain entities + Repositories + Services for protocols  
**Where**: `src/modules/analysis_engine/` (new directories)  
**Impact**: Enable protocol tracking

### **Phase 3: Protocol API + Integration (ADR-021 Phase 3-4)**
**Timeline**: 1-2 weeks  
**What**: API endpoints + Integration tests  
**Where**: `src/modules/analysis_engine/api_component/`  
**Impact**: Enable UI to show protocol status

### **Phase 4: Unified Analysis Service (Bridge)**
**Timeline**: 1 week  
**What**: OrchestrationService that combines Protocol + Analysis  
**Where**: `src/modules/analysis_engine/service_component/`  
**Impact**: Smart decisions based on both engines

### **Phase 5: ML Preparation (Post-MVP)**
**Timeline**: TBD (Q3 2026?)  
**What**: Feature engineering, data collection, model training  
**Impact**: Predictive capabilities

---

## 📝 CONTEXTO FILES: WHAT TO UPDATE

### **1. Update: project-context.md**

```
SECTION: "System modules"

CHANGE FROM:
- **Analysis Engine Module**: Real-time comparison, status assessment, 
  and recommendation generation

CHANGE TO:
- **Analysis Engine Module**: 
  - Real-time comparison, status assessment, recommendation generation (ADR-020)
  - Fermentation protocol tracking, compliance auditing, operational guidance (ADR-021)
  - Integration: Unified analysis combining anomaly detection + protocol compliance
```

### **2. Update: ADR-INDEX.md**

```
ADD ENTRY:
| **[ADR-021](./ADR-021-protocol-compliance-engine.md)** | 
  Fermentation Protocol Compliance Engine | 
  📋 Proposed | 
  2026-02-06 | 
  High |
```

### **3. CREATE: src/modules/analysis_engine/.ai-context/module-context.md**

```
New file with full module documentation including:
- Both ADR-020 (Analysis Engine) and ADR-021 (Protocol Engine) status
- Data model (entities, enums, interfaces)
- Service layer (both engines + unified orchestrator)
- API endpoints (both engines)
- Test coverage expectations
- Implementation timeline
- DDD context mapping
```

---

## 🎓 VISUALIZATION TOOLS (Para entender la arquitectura)

**Recomendado crear** (Future visual aids):

```
1. ENTIDAD-RELACIÓN DIAGRAM (Protocol + Analysis Entities)
   └─ Mostrar cómo se relacionan las tablas de ambos engines

2. SERVICE INTERACTION DIAGRAM
   └─ Mostrar cómo ProtocolService + AnalysisService → UnifiedAnalysisService

3. DATA FLOW DIAGRAM
   └─ Cómo fluye información desde Fermentation → Protocol → Analysis → Decision

4. TIMELINE DIAGRAM
   └─ Phases 1-5 de ADR-020 + ADR-021, paralelos o secuenciales?

5. ELEVATION LOGIC MATRIX
   └─ When Protocol OK vs Anomaly → What severity?
```

---

## ✅ CONCLUSIÓN

**Protocol Engine (ADR-021) va:**
- ✅ En `src/modules/analysis_engine/` (mismo bounded context que Analysis Engine)
- ✅ Como módulo separado con su propio dominio/service/api
- ✅ Conectado via UnifiedAnalysisService que orquesta ambos
- ✅ Primero el dominio (Phase 1-2), luego API (Phase 3-4)

**ML es:**
- ✅ **Post-MVP** (No en alcance actual)
- ✅ Fundación se prepara ahora (data collection via ProtocolExecution)
- ✅ Será Phase 5+ en future roadmap

**Actualizar contextos:**
- ✅ project-context.md (documentar ambos engines)
- ✅ ADR-INDEX.md (agregar ADR-021)
- ✅ Crear analysis_engine module-context.md (nuevo)


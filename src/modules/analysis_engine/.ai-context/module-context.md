# Module Context: Analysis Engine

> **Parent Context**: See `/.ai-context/project-context.md` for system-level decisions
> **Collaboration Guidelines**: See `/.ai-context/collaboration-principles.md`

## Module responsibility

**Intelligent anomaly detection and recommendation engine** for real-time fermentation monitoring.

**Position in system**: Consumes fermentation time-series data produced by the Fermentation module, applies statistical comparison against historical baselines, detects anomalies, generates actionable recommendations, and (via ADR-037) integrates bidirectionally with the Protocol Engine.

## Technology stack

- **Framework**: FastAPI (Python 3.9+) — independent service on port **8001**
- **Database**: PostgreSQL with SQLAlchemy ORM (AsyncSession + JSONB columns)
- **Validation**: Pydantic V2 models for request/response handling
- **Testing**: pytest with `unittest.mock.AsyncMock` (JSONB-compatible session mocking)
- **Dependency management**: Independent **Poetry** virtual environment
- **Logging**: Loguru for structured logging
- **Code Quality**: Black (formatting), flake8 (linting)

## Module interfaces

**Receives from**: Fermentation module — fermentation history, current readings, protocol compliance scores  
**Provides to**: Frontend — analysis results, anomaly alerts, recommendations, protocol advisories  
**Depends on**: Authentication module (JWT validation), Fermentation module (historical data + protocol status)

## Key functionality

- **Analysis orchestration**: Coordinate comparison → anomaly detection → recommendation pipeline
- **Comparison engine**: Compare current fermentation readings against historical baselines
- **Anomaly detection**: Multi-signal detection (glucose, ethanol, temperature, density) with severity scoring
- **Recommendation engine**: Template-driven actionable suggestions based on anomaly patterns
- **Protocol integration** (ADR-037 🔄 In Progress):
  - Confidence boost from protocol compliance score
  - Protocol advisory generation from anomaly analysis
  - Analysis recalibration on protocol changes

## Business rules

- **Confidence formula (ADR-020)**: `confidence = 0.7×pattern_match + 0.2×sample_count_norm + 0.1×recency`
- **Protocol confidence boost (ADR-037)**: `adjusted_confidence = base_confidence × (0.5 + compliance_score / 100.0)`
- **Anomaly severity**: CRITICAL → HIGH → MEDIUM → LOW cascade thresholds
- **Deviation scoring**: Normalized distance from historical mean with sigma bands
- **User isolation**: All analyses scoped by `winery_id` (multi-tenancy via ADR-025)
- **Recommendation templates**: Reusable, category-tagged templates linked to `AnomalyType`

## Module components

### Domain Layer (`src/domain/`) — ✅ COMPLETE

**Entities** (`src/domain/entities/`):
| Entity | Responsibility |
|--------|---------------|
| `Analysis` | Root aggregate — links fermentation to analysis result with confidence, status, timestamp |
| `Anomaly` | Detected deviation with type, severity, deviation score, affected metric |
| `Recommendation` | Actionable suggestion derived from anomaly, linked to template |
| `RecommendationTemplate` | Reusable template with category, priority, message pattern |

**Value Objects** (`src/domain/value_objects/`):
| Value Object | Description |
|--------------|-------------|
| `ComparisonResult` | Immutable result of baseline comparison (mean, sigma, deviation) |
| `ConfidenceLevel` | Validated float [0.0–1.0] representing analysis confidence |
| `DeviationScore` | Normalized deviation magnitude with direction (above/below) |

**Enums** (`src/domain/enums/`):
| Enum | Values |
|------|--------|
| `AnalysisStatus` | PENDING, IN_PROGRESS, COMPLETED, FAILED |
| `AnomalyType` | GLUCOSE_STALL, ETHANOL_DROP, TEMP_SPIKE, DENSITY_ANOMALY, ... |
| `RecommendationCategory` | IMMEDIATE_ACTION, MONITORING, PREVENTIVE, INFORMATIONAL |
| `SeverityLevel` | CRITICAL, HIGH, MEDIUM, LOW |

**Repository Interfaces** (`src/domain/repositories/`):
- `IAnalysisRepository` — CRUD + status queries
- `IAnomalyRepository` — anomalies by analysis, severity filter
- `IRecommendationRepository` — recommendations by analysis/category
- `IRecommendationTemplateRepository` — template lookup by anomaly type

### Repository Component (`src/repository_component/`) — ✅ COMPLETE

**Concrete Repositories** (`src/repository_component/repositories/`):
- `AnalysisRepository` — SQLAlchemy async implementation of `IAnalysisRepository`
- `AnomalyRepository` — with JSONB field handling for deviation metadata
- `RecommendationRepository` — with template JOIN queries
- `RecommendationTemplateRepository` — bulk template loading + anomaly type lookup

**ORM Models** (`src/repository_component/models/`):
- Shared base: `src.shared.infra.orm.base_entity.Base` (imported before fermentation models in conftest to avoid mapper cascade errors)

### Service Component (`src/service_component/`) — ✅ COMPLETE

**Services** (`src/service_component/services/`):
| Service | Responsibility |
|---------|---------------|
| `AnalysisOrchestratorService` | Coordinates the full analysis pipeline; entry point for triggering analysis |
| `ComparisonService` | Computes `ComparisonResult` by comparing current values to historical baselines |
| `AnomalyDetectionService` | Applies threshold rules to `ComparisonResult` → generates `Anomaly` list |
| `RecommendationService` | Maps anomalies to `RecommendationTemplate` → creates `Recommendation` list |
| `ProtocolAnalysisIntegrationService` | **(ADR-037 🔄)** Applies confidence boost, generates `ProtocolAdvisory` |

### API Layer (`src/api/`) — ✅ COMPLETE

**Routers** (`src/api/routers/`):
- `analysis_router.py` — Analysis lifecycle endpoints (trigger, get, list, status)
- `recommendation_router.py` — Recommendation retrieval and template management

**Schemas** (`src/api/schemas/`):
- `requests/` — Pydantic V2 input models for all endpoints
- `responses/` — Pydantic V2 output models (including nested anomaly + recommendation data)

**Infrastructure** (`src/api/`):
- `dependencies.py` — FastAPI dependency injection (repositories, services, auth)
- `error_handlers.py` — Centralized `@handle_analysis_errors` decorator; maps domain exceptions → HTTP codes

**Port**: `8001` (configured in `src/main.py`)

## Implementation status

**Status**: ✅ **Domain + Repository + Service + API — Fully Implemented**  
**Last Updated**: March 1, 2026  
**ADR References**:
- [ADR-020](../../.ai-context/adr/ADR-020-analysis-engine-architecture.md) — Analysis Engine Architecture ✅ **Implemented**
- [ADR-037](../../.ai-context/adr/ADR-037-protocol-analysis-integration.md) — Protocol↔Analysis Integration 🔄 **In Progress**

### Test Summary

| Layer | File | Tests |
|-------|------|-------|
| Service | `test_analysis_orchestrator_service.py` | ~30 |
| Service | `test_comparison_service.py` | ~20 |
| Service | `test_anomaly_detection_service.py` | ~25 |
| Service | `test_recommendation_service.py` | ~20 |
| API | `test_analysis_api.py` | ~13 |
| **Total** | | **108 passing** ✅ |

### Test execution

```powershell
# From analysis_engine module directory
Set-Location "c:\dev\wine-fermentation-system\src\modules\analysis_engine"
poetry run pytest "../../../tests/unit/modules/analysis_engine/" -q

# System-wide (all 1,344 tests)
Set-Location "c:\dev\wine-fermentation-system"
.\run_all_tests.ps1
```

### Critical test setup notes

1. **Pre-import base entity**: In `tests/unit/modules/analysis_engine/conftest.py`, `src.shared.infra.orm.base_entity` must be imported **before** fermentation ORM models to avoid SQLAlchemy mapper cascade failures
2. **AsyncMock sessions**: JSONB columns require `AsyncMock` (not `MagicMock`) for SQLAlchemy async compatibility
3. **Isolated venv**: All tests run inside the analysis_engine Poetry virtual environment

## ADR-037 Protocol Integration (🔄 In Progress — March 1, 2026)

### Integration flows

```
1. CONFIDENCE BOOST (real-time)
   ProtocolExecution.compliance_score
        ↓
   ProtocolAnalysisIntegrationService.boost_confidence()
        ↓  multiplier = 0.5 + compliance_score / 100.0
   AnalysisOrchestratorService (adjusted confidence)

2. PROTOCOL ADVISORY (batch, post-analysis)
   Analysis + Anomaly list
        ↓
   ProtocolAnalysisIntegrationService.generate_advisory()
        ↓  map AnomalyType → StepType suggestion
   ProtocolAdvisory (entity, advisory_type, target_step_type)

3. ANALYSIS RECALIBRATION (event-driven)
   ProtocolExecution status change
        ↓ event / webhook
   AnalysisOrchestratorService.recalibrate()
```

### Formula

$$\text{adjusted\_confidence} = \min\left(\text{base\_confidence} \times \left(0.5 + \frac{\text{compliance\_score}}{100.0}\right),\ 1.0\right)$$

### Files to create (ADR-037 implementation)

```
src/modules/analysis_engine/src/
  domain/
    entities/
      protocol_advisory.py         ← NEW: ProtocolAdvisory entity
    enums/
      advisory_type.py             ← NEW: ACCELERATE_STEP, SKIP_STEP, ADD_STEP
  service_component/
    services/
      protocol_integration_service.py  ← NEW: ProtocolAnalysisIntegrationService

tests/unit/modules/analysis_engine/
  service/
    test_protocol_integration_service.py  ← NEW: ~20 tests
```

## Domain entities (quick reference)

```python
# Core analysis aggregate
Analysis(id, fermentation_id, winery_id, status, confidence, triggered_at, completed_at)

# Detected deviation
Anomaly(id, analysis_id, anomaly_type, severity, deviation_score, metric_name, current_value, expected_value)

# Actionable suggestion
Recommendation(id, analysis_id, template_id, category, priority, message, action_required)

# Reusable template
RecommendationTemplate(id, anomaly_type, category, priority, message_template, action_template)
```

## DDD implementation

**Dependency direction** (all arrows point inward toward Domain):

```
api_component
     │
service_component
     │
repository_component
     │
     └──────────────── domain (entities, value_objects, enums, repository interfaces)
```

**Multi-tenancy**: All queries scoped by `winery_id`  
**No cross-module ORM relationships**: Cross-module data fetched via HTTP or plain integer foreign keys (same pattern as Protocol Engine — ADR-035)

## How to work on this module

1. Check ADRs: `ADR-020` (architecture), `ADR-037` (protocol integration), `ADR-025` (multi-tenancy)
2. Run tests: `poetry run pytest "../../../tests/unit/modules/analysis_engine/" -q` (108 tests)
3. Component entry points:
   - **Service**: `src/service_component/services/analysis_orchestrator_service.py`
   - **API**: `src/api/routers/analysis_router.py` + `recommendation_router.py`
   - **Domain**: `src/domain/entities/analysis.py`
4. For ADR-037: start with `ProtocolAnalysisIntegrationService`, then `ProtocolAdvisory` entity

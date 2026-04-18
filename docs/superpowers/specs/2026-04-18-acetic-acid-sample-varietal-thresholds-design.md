# Design Spec: AceticAcidSample + Varietal Threshold Configuration

**Date:** 2026-04-18  
**Status:** Approved  
**Scope:** Option A — data layer + detection logic only. No API endpoint (frontend pending).  
**Modules affected:** `fermentation`, `analysis_engine`

---

## Problem

1. `AnomalyDetectionService.detect_volatile_acidity()` is a TODO — blocked because `SampleType` has no acidity value and no sample entity exists for acetic acid measurements. Three tests are permanently skipped as a result.
2. All anomaly detection thresholds are hardcoded as magic numbers scattered across `AnomalyDetectionService`. They cannot be changed without a code deploy, and they do not vary by varietal or winery.

## Goals

- Add `AceticAcidSample` entity + `SampleType.ACETIC_ACID` enum value to the `fermentation` module.
- Add `ThresholdConfigService` to `analysis_engine` — loads thresholds from a TOML file at startup, resolves them by varietal.
- Refactor `AnomalyDetectionService` to use `ThresholdConfigService` instead of hardcoded constants.
- Implement `detect_volatile_acidity()` and remove the 3 skipped tests.
- Update `.ai-context` files to document the extension path for future acids and per-winery threshold overrides.

## Non-goals (deferred to Option B)

- `POST /fermentations/{id}/samples/acetic-acid` API endpoint (requires frontend).
- `LacticAcidSample`, `SulfurDioxideSample` (same pattern, add when needed).
- Per-winery threshold overrides via DB table `winery_varietal_thresholds` (see migration path below).

---

## Architecture

### Dependency direction (unchanged)

```
api_component
     │
service_component  ←  ThresholdConfigService (new)
     │                    │
     │               config/thresholds.toml (new)
repository_component
     │
domain (entities, value_objects, enums)
```

`ThresholdConfigService` lives in `service_component` — it is infrastructure for detection logic, not domain logic itself.

---

## New files

### 1. `src/modules/fermentation/src/domain/entities/samples/acetic_acid_sample.py`

Follows the exact pattern of `DensitySample` and `CelsiusTemperatureSample`. No extra columns — the measurement goes in `BaseSample.value` (g/L of acetic acid).

```python
class AceticAcidSample(BaseSample):
    """Acetic acid (volatile acidity) measurement in g/L.
    
    Measures the primary volatile acid in wine.
    Normal range: < 0.6 g/L
    Warning:      0.6 – 0.8 g/L
    Critical:     > 0.8 g/L  (acetification risk)
    
    Future samples to add with the same pattern:
      - LacticAcidSample  (g/L) — malolactic fermentation monitoring
      - SulfurDioxideSample (mg/L) — SO₂ preservation monitoring
    """
    __mapper_args__ = {"polymorphic_identity": "acetic_acid"}

    def __init__(self, **kwargs):
        kwargs["units"] = "g/L"
        super().__init__(**kwargs)
```

### 2. `src/modules/fermentation/src/domain/entities/samples/__init__.py` (modified)

Add `'AceticAcidSample'` to `__all__`. No import needed — the file intentionally avoids imports to prevent SQLAlchemy mapper conflicts during pytest discovery (existing pattern).

### 3. `src/modules/fermentation/src/domain/enums/sample_type.py` (modified)

Add `ACETIC_ACID = "acetic_acid"` to the existing `SampleType` enum.

### 3. `src/modules/analysis_engine/config/thresholds.toml` (new)

```toml
# Anomaly detection thresholds by varietal
# 
# MIGRATION PATH → per-winery DB overrides (Option B):
#   1. Create table: winery_varietal_thresholds(winery_id, varietal_group, key, value)
#   2. ThresholdConfigService.get_thresholds(variety, winery_id=None):
#      - If winery_id: SELECT from DB, fallback to this file on miss
#      - If no winery_id: use this file only
#   This file becomes the global default — no schema changes to detection logic needed.

[defaults]
# Applied when a varietal is not explicitly categorised as red
volatile_acidity_warning_g_l  = 0.6
volatile_acidity_critical_g_l = 0.8
density_drop_max_pct_24h       = 15.0
h2s_risk_temp_threshold_c      = 18.0
h2s_risk_max_days              = 10.0
stuck_min_density_change       = 1.0
stuck_min_time_span_days       = 0.5

[varietals.red]
# Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temp_critical_min_c  = 23.9   # 75°F — yeast death below
temp_critical_max_c  = 32.2   # 90°F — yeast death above
temp_optimal_min_c   = 24.0
temp_optimal_max_c   = 30.0

[varietals.white]
# All other varietals (whites, rosés) — also the fallback category
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temp_critical_min_c  = 11.7   # 53°F
temp_critical_max_c  = 16.7   # 62°F
temp_optimal_min_c   = 12.0
temp_optimal_max_c   = 16.0
```

### 4. `src/modules/analysis_engine/src/service_component/services/threshold_config_service.py` (new)

```python
@dataclass(frozen=True)
class VarietalThresholds:
    # Temperature
    temp_critical_min_c: float
    temp_critical_max_c: float
    temp_optimal_min_c: float
    temp_optimal_max_c: float
    # Volatile acidity
    volatile_acidity_warning_g_l: float
    volatile_acidity_critical_g_l: float
    # Density
    density_drop_max_pct_24h: float
    # H2S
    h2s_risk_temp_threshold_c: float
    h2s_risk_max_days: float
    # Stuck fermentation
    stuck_min_density_change: float
    stuck_min_time_span_days: float


RED_VARIETALS = {"CABERNET SAUVIGNON", "MERLOT", "PINOT NOIR", "ZINFANDEL"}


class ThresholdConfigService:
    """
    Loads anomaly detection thresholds from config/thresholds.toml.
    Resolves to varietal group (red / white) at runtime.

    Loaded once at application startup — pass as a dependency to AnomalyDetectionService.

    FUTURE — per-winery overrides (Option B):
        Change signature to: get_thresholds(variety: str, winery_id: UUID | None = None)
        Implementation: query winery_varietal_thresholds table, fallback to TOML on miss.
        No changes needed in AnomalyDetectionService — interface is identical.
    """
    def __init__(self, config_path: Path | None = None): ...
    def get_thresholds(self, variety: str) -> VarietalThresholds: ...
```

Load uses `tomllib` (stdlib in Python 3.11+) or `tomli` (backport for 3.9). Since analysis_engine targets Python 3.9, add `tomli` to `pyproject.toml` dependencies.

---

## Modified files

### 5. `src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py`

**`__init__` change:**
```python
def __init__(self, session: AsyncSession, threshold_config: ThresholdConfigService):
    self.session = session
    self.config = threshold_config
```

**`detect_all_anomalies()` signature change** — add optional parameter:
```python
async def detect_all_anomalies(
    self,
    ...
    volatile_acidity_g_l: Optional[float] = None,   # ← NEW
) -> List[Anomaly]:
```

Each detection method receives `thresholds = self.config.get_thresholds(variety)` and uses `thresholds.temp_critical_min_c` etc. instead of hardcoded literals.

**New method:**
```python
def detect_volatile_acidity(
    self,
    volatile_acidity_g_l: float,
    thresholds: VarietalThresholds,
) -> Optional[Anomaly]:
    if volatile_acidity_g_l > thresholds.volatile_acidity_critical_g_l:
        severity = SeverityLevel.CRITICAL
    elif volatile_acidity_g_l > thresholds.volatile_acidity_warning_g_l:
        severity = SeverityLevel.WARNING
    else:
        return None
    # build and return Anomaly(VOLATILE_ACIDITY_HIGH, severity, ...)
```

### 6. `src/modules/analysis_engine/src/api/dependencies.py`

Instantiate `ThresholdConfigService` once via FastAPI `lifespan` and expose as a FastAPI dependency. Inject into `AnomalyDetectionService` via the existing dependency injection pattern.

---

## Tests

### Unlocked (remove `@pytest.mark.skip`):
| Test | Scenario |
|------|----------|
| `test_volatile_acidity_critical` | value > 0.8 → CRITICAL anomaly |
| `test_volatile_acidity_warning` | value 0.6–0.8 → WARNING anomaly |
| `test_volatile_acidity_no_anomaly` | value < 0.6 → None |

### New unit tests:
- `tests/unit/service/test_threshold_config_service.py`
  - Loads default thresholds correctly
  - Resolves red varietals (Cabernet → red group)
  - Resolves unknown varietal to white/defaults
  - Returns frozen `VarietalThresholds` dataclass
  - Raises on missing/malformed TOML

### Existing tests — impact:
- `test_anomaly_detection_service.py` — all tests that instantiate `AnomalyDetectionService` must pass a `ThresholdConfigService` (or a mock). Add a `threshold_config` fixture to `conftest.py` using a test TOML or a `MagicMock`.
- `test_analysis_orchestrator_service.py` — orchestrator creates `AnomalyDetectionService` internally; mock `ThresholdConfigService` at the orchestrator boundary.

---

## `.ai-context` updates

### `fermentation/src/domain/.ai-context/component-context.md`
Add to samples table:
- `AceticAcidSample` — acetic acid in g/L, `polymorphic_identity: "acetic_acid"`

Add extension note:
> **Adding a new sample type:** create `<name>_sample.py` extending `BaseSample`, set `polymorphic_identity` and default `units` in `__init__`. Add enum value to `SampleType`. No migrations needed (STI — all rows share the `samples` table). Planned: `LacticAcidSample` (g/L), `SulfurDioxideSample` (mg/L).

### `analysis_engine/src/service_component/.ai-context/component-context.md`
Add `ThresholdConfigService` to services table. Document:
- Config file location: `config/thresholds.toml`
- Varietal groups: `red` (Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel) / `white` (all others)
- Migration path to per-winery DB overrides (Option B): change `get_thresholds(variety)` to `get_thresholds(variety, winery_id)`, add `winery_varietal_thresholds` table, fallback to TOML

---

## Migration path to Option B (per-winery DB overrides)

When the first client is onboarded:

1. Add table `winery_varietal_thresholds(id, winery_id UUID, varietal_group VARCHAR, key VARCHAR, value FLOAT)` to `analysis_engine` DB
2. Change `ThresholdConfigService.get_thresholds(variety: str)` → `get_thresholds(variety: str, winery_id: UUID | None = None)`
3. Implementation: query DB for winery overrides, fall back to TOML values on miss
4. `AnomalyDetectionService` signature **does not change** — it calls `self.config.get_thresholds(variety)` and `winery_id` is threaded through the orchestrator → config service
5. Seed the DB table from `thresholds.toml` values on first winery setup

**No changes to detection logic are required for this migration.**

---

## Dependency addition

Add to `analysis_engine/pyproject.toml`:
```toml
tomli = {version = "^2.0", python = "<3.11"}
```
Python 3.11+ has `tomllib` in stdlib; `tomli` is only needed for 3.9/3.10.

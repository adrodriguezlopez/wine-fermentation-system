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

## Development methodology: TDD (religioso)

Every step below follows RED → GREEN → REFACTOR:

1. 🔴 **RED** — write the failing test first (it must fail for the right reason)
2. 🟢 **GREEN** — write the minimum implementation to make it pass
3. 🔵 **REFACTOR** — clean up while keeping tests green

**No production code is written before its test exists.** This applies to every new class, method, and config file in this spec.

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
      - LacticAcidSample    (g/L)  — malolactic fermentation monitoring
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

### 4. `src/modules/analysis_engine/config/thresholds.toml` (new)

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
volatile_acidity_warning_in_grams_per_liter  = 0.6
volatile_acidity_critical_in_grams_per_liter = 0.8
density_drop_max_percent_per_24_hours        = 15.0
hydrogen_sulfide_risk_max_temperature_celsius = 18.0
hydrogen_sulfide_risk_critical_window_days    = 10.0
stuck_fermentation_min_density_change_points  = 1.0
stuck_fermentation_min_stall_duration_days    = 0.5

[varietals.red]
# Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temperature_critical_min_celsius  = 23.9   # 75°F — yeast death below
temperature_critical_max_celsius  = 32.2   # 90°F — yeast death above
temperature_optimal_min_celsius   = 24.0
temperature_optimal_max_celsius   = 30.0

[varietals.white]
# All other varietals (whites, rosés) — also the fallback category
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temperature_critical_min_celsius  = 11.7   # 53°F
temperature_critical_max_celsius  = 16.7   # 62°F
temperature_optimal_min_celsius   = 12.0
temperature_optimal_max_celsius   = 16.0
```

### 5. `src/modules/analysis_engine/src/service_component/services/threshold_config_service.py` (new)

```python
@dataclass(frozen=True)
class VarietalThresholds:
    # Temperature limits
    temperature_critical_min_celsius: float
    temperature_critical_max_celsius: float
    temperature_optimal_min_celsius: float
    temperature_optimal_max_celsius: float
    # Volatile acidity thresholds
    volatile_acidity_warning_in_grams_per_liter: float
    volatile_acidity_critical_in_grams_per_liter: float
    # Density drop rate
    density_drop_max_percent_per_24_hours: float
    # Hydrogen sulfide risk conditions
    hydrogen_sulfide_risk_max_temperature_celsius: float
    hydrogen_sulfide_risk_critical_window_days: float
    # Stuck fermentation detection
    stuck_fermentation_min_density_change_points: float
    stuck_fermentation_min_stall_duration_days: float


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

### 6. `src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py`

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
    volatile_acidity_in_grams_per_liter: Optional[float] = None,   # ← NEW
) -> List[Anomaly]:
```

Each detection method receives `thresholds = self.config.get_thresholds(variety)` and uses
`thresholds.temperature_critical_min_celsius` etc. instead of hardcoded literals.

**New method:**
```python
def detect_volatile_acidity(
    self,
    volatile_acidity_in_grams_per_liter: float,
    thresholds: VarietalThresholds,
) -> Optional[Anomaly]:
    if volatile_acidity_in_grams_per_liter > thresholds.volatile_acidity_critical_in_grams_per_liter:
        severity = SeverityLevel.CRITICAL
    elif volatile_acidity_in_grams_per_liter > thresholds.volatile_acidity_warning_in_grams_per_liter:
        severity = SeverityLevel.WARNING
    else:
        return None
    # build and return Anomaly(VOLATILE_ACIDITY_HIGH, severity, ...)
```

### 7. `src/modules/analysis_engine/src/api/dependencies.py`

Instantiate `ThresholdConfigService` once via FastAPI `lifespan` and expose as a FastAPI dependency. Inject into `AnomalyDetectionService` via the existing dependency injection pattern.

---

## TDD implementation order

Each step = one RED → GREEN → REFACTOR cycle. Do not advance to the next step until all tests from the current step are green.

### Step 1 — `AceticAcidSample` entity (fermentation module)
🔴 Write `tests/unit/domain/test_acetic_acid_sample.py`:
  - `AceticAcidSample` sets `units = "g/L"` by default
  - `polymorphic_identity` is `"acetic_acid"`
  - `SampleType.ACETIC_ACID` value is `"acetic_acid"`
  - `SampleType` has exactly 4 members (guard test — fails if we forget to add it)

🟢 Create `acetic_acid_sample.py`, add `ACETIC_ACID` to `SampleType`, update `__init__.py __all__`.

🔵 Confirm no existing fermentation tests broken. Run full suite.

### Step 2 — `ThresholdConfigService` (analysis_engine)
🔴 Write `tests/unit/service/test_threshold_config_service.py`:
  - Loads `thresholds.toml` and returns a `VarietalThresholds` instance
  - Cabernet Sauvignon resolves to red group (`temperature_critical_min_celsius == 23.9`)
  - Chardonnay resolves to white/defaults (`temperature_critical_min_celsius == 11.7`)
  - Unknown varietal falls back to white/defaults
  - Returned object is frozen (`raises FrozenInstanceError on mutation attempt`)
  - Raises `FileNotFoundError` (or custom `ThresholdConfigError`) on missing TOML

🟢 Create `thresholds.toml` and `threshold_config_service.py`.

🔵 Confirm `VarietalThresholds` field names match TOML keys exactly.

### Step 3 — Refactor `AnomalyDetectionService` to use thresholds
🔴 Update existing tests in `test_anomaly_detection_service.py`:
  - Add `threshold_config` fixture to `conftest.py` (real `ThresholdConfigService` pointing at a test TOML, or `MagicMock` with preset return values)
  - All existing tests must still pass after refactor — no behavior change, only source of values changes

🟢 Inject `ThresholdConfigService` into `AnomalyDetectionService.__init__`. Replace all hardcoded literals with `thresholds.*` field references.

🔵 No magic numbers remain in detection methods.

### Step 4 — `detect_volatile_acidity()` — unlock the 3 skipped tests
🔴 Remove `@pytest.mark.skip` from the 3 tests in `test_anomaly_detection_service.py`. They must now fail (RED) because the method doesn't exist yet.

🟢 Implement `detect_volatile_acidity()`.

🔵 All 3 previously-skipped tests pass. Total skipped count drops from 7 to 4 (the 4 integration-covered ones remain as documented).

### Step 5 — Wire `dependencies.py` + update orchestrator tests
🔴 Update `test_analysis_orchestrator_service.py` to mock `ThresholdConfigService` at the orchestrator boundary.

🟢 Update `dependencies.py` to instantiate `ThresholdConfigService` in `lifespan`.

🔵 Full test suite green. No regressions.

### Step 6 — Update `.ai-context` files
No tests for documentation, but this step is mandatory before closing the feature.
- `fermentation/src/domain/.ai-context/component-context.md`
- `analysis_engine/src/service_component/.ai-context/component-context.md`

---

## Tests summary

| File | Tests | Notes |
|------|-------|-------|
| `fermentation/tests/unit/domain/test_acetic_acid_sample.py` | ~4 | NEW |
| `analysis_engine/tests/unit/service/test_threshold_config_service.py` | ~6 | NEW |
| `analysis_engine/tests/unit/service/test_anomaly_detection_service.py` | +3 unskipped | Remove `@pytest.mark.skip` |
| `analysis_engine/tests/unit/service/test_analysis_orchestrator_service.py` | 0 new | Update fixtures only |
| `analysis_engine/tests/conftest.py` | 0 new | Add `threshold_config` fixture |

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
- `VarietalThresholds` is a frozen dataclass — all field names are fully descriptive (no abbreviations)
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

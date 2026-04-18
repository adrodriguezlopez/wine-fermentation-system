# AceticAcidSample + Varietal Threshold Configuration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `AceticAcidSample` entity to the fermentation module and introduce `ThresholdConfigService` to the analysis engine so all anomaly detection thresholds are loaded from `thresholds.toml` by varietal instead of being hardcoded — unlocking the 3 previously-skipped volatile acidity tests.

**Architecture:** `AceticAcidSample` follows the existing STI (single-table inheritance) pattern on the `samples` table — no schema migration needed. `ThresholdConfigService` is a new class in `analysis_engine/service_component` that loads a TOML file at startup and resolves thresholds to a frozen `VarietalThresholds` dataclass by varietal group. `AnomalyDetectionService` receives `ThresholdConfigService` via constructor injection and uses it instead of hardcoded literals.

**Tech Stack:** Python 3.9, FastAPI, SQLAlchemy 2.0 async, `tomli` (TOML parser backport for Python <3.11), pytest with `AsyncMock`, Poetry (two separate venvs: `fermentation` and `analysis_engine`).

---

## File Map

### New files
| File | Responsibility |
|------|---------------|
| `src/modules/fermentation/src/domain/entities/samples/acetic_acid_sample.py` | STI subclass of `BaseSample`, units="g/L", polymorphic_identity="acetic_acid" |
| `src/modules/fermentation/tests/unit/domain/test_acetic_acid_sample.py` | Tests for `AceticAcidSample` entity and `SampleType.ACETIC_ACID` |
| `src/modules/analysis_engine/config/thresholds.toml` | Varietal threshold values (red/white groups + shared defaults) |
| `src/modules/analysis_engine/config/thresholds_test.toml` | Predictable threshold values for unit tests |
| `src/modules/analysis_engine/src/service_component/services/threshold_config_service.py` | `VarietalThresholds` dataclass + `ThresholdConfigService` loader |
| `src/modules/analysis_engine/tests/unit/service/test_threshold_config_service.py` | Tests for threshold loading and varietal resolution |

### Modified files
| File | Change |
|------|--------|
| `src/modules/fermentation/src/domain/entities/samples/__init__.py` | Add `'AceticAcidSample'` to `__all__` |
| `src/modules/fermentation/src/domain/enums/sample_type.py` | Add `ACETIC_ACID = "acetic_acid"` |
| `src/modules/analysis_engine/pyproject.toml` | Add `tomli` dependency (Python <3.11 backport) |
| `src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py` | Inject `ThresholdConfigService`; replace hardcoded literals; add `detect_volatile_acidity()` |
| `src/modules/analysis_engine/src/service_component/services/analysis_orchestrator_service.py` | Pass `ThresholdConfigService` when constructing `AnomalyDetectionService` |
| `src/modules/analysis_engine/src/api/dependencies.py` | Instantiate `ThresholdConfigService` as a module-level singleton |
| `src/modules/analysis_engine/tests/conftest.py` | Add `threshold_config` fixture (uses `thresholds_test.toml`) |
| `src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py` | Update `service` fixture; remove 3 `@pytest.mark.skip`; update 3 test signatures |
| `src/modules/analysis_engine/tests/unit/service/test_analysis_orchestrator_service.py` | No new tests — `AnalysisOrchestratorService(session=...)` still works (threshold_config internal) |
| `src/modules/fermentation/src/domain/.ai-context/component-context.md` | Document `AceticAcidSample` + extension pattern |
| `src/modules/analysis_engine/src/service_component/.ai-context/component-context.md` | Document `ThresholdConfigService` + migration path |

---

## Task 1: AceticAcidSample entity (fermentation module)

**Files:**
- Create: `src/modules/fermentation/src/domain/entities/samples/acetic_acid_sample.py`
- Modify: `src/modules/fermentation/src/domain/entities/samples/__init__.py`
- Modify: `src/modules/fermentation/src/domain/enums/sample_type.py`
- Create: `src/modules/fermentation/tests/unit/domain/test_acetic_acid_sample.py`

- [ ] **Step 1: Write the failing tests**

Create `src/modules/fermentation/tests/unit/domain/test_acetic_acid_sample.py`:

```python
"""
TDD tests for AceticAcidSample entity and SampleType.ACETIC_ACID enum value.
RED: All tests fail because neither class nor enum value exist yet.
"""
import pytest
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


class TestSampleTypeAceticAcid:
    def test_acetic_acid_enum_value_exists(self):
        assert SampleType.ACETIC_ACID.value == "acetic_acid"

    def test_sample_type_has_exactly_four_members(self):
        # Guard test: fails if we add a member without updating this count.
        assert len(SampleType) == 4

    def test_acetic_acid_is_string_enum(self):
        assert isinstance(SampleType.ACETIC_ACID, str)


class TestAceticAcidSample:
    def test_default_units_are_grams_per_liter(self):
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )
        from datetime import datetime, timezone

        sample = AceticAcidSample(
            fermentation_id=1,
            recorded_at=datetime.now(timezone.utc),
            recorded_by_user_id=1,
            value=0.5,
        )
        assert sample.units == "g/L"

    def test_polymorphic_identity_is_acetic_acid(self):
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )
        assert AceticAcidSample.__mapper_args__["polymorphic_identity"] == "acetic_acid"

    def test_units_cannot_be_overridden(self):
        """Units are always g/L — the constructor enforces this."""
        from src.modules.fermentation.src.domain.entities.samples.acetic_acid_sample import (
            AceticAcidSample,
        )
        from datetime import datetime, timezone

        sample = AceticAcidSample(
            fermentation_id=1,
            recorded_at=datetime.now(timezone.utc),
            recorded_by_user_id=1,
            value=0.7,
            units="wrong_unit",  # should be overwritten
        )
        assert sample.units == "g/L"
```

- [ ] **Step 2: Run tests to confirm RED**

```
cd src/modules/fermentation
poetry run pytest tests/unit/domain/test_acetic_acid_sample.py -v
```

Expected: 6 failures — `ImportError: cannot import name 'AceticAcidSample'` and `AttributeError: ACETIC_ACID`.

- [ ] **Step 3: Add ACETIC_ACID to SampleType enum**

Edit `src/modules/fermentation/src/domain/enums/sample_type.py`:

```python
from enum import Enum


class SampleType(str, Enum):
    """Supported sample measurement types."""

    SUGAR = "sugar"
    TEMPERATURE = "temperature"
    DENSITY = "density"
    ACETIC_ACID = "acetic_acid"
```

- [ ] **Step 4: Create AceticAcidSample entity**

Create `src/modules/fermentation/src/domain/entities/samples/acetic_acid_sample.py`:

```python
from typing import Any
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class AceticAcidSample(BaseSample):
    """Acetic acid (volatile acidity) measurement in g/L.

    Measures the primary volatile acid in wine. The value field (inherited
    from BaseSample) stores the concentration in grams per litre.

    Normal range: < 0.6 g/L
    Warning:      0.6 – 0.8 g/L
    Critical:     > 0.8 g/L  (acetification risk — immediate intervention required)

    Future samples to add with the same pattern:
      - LacticAcidSample    (g/L)  — malolactic fermentation monitoring
      - SulfurDioxideSample (mg/L) — SO₂ preservation monitoring

    Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)
    """

    __mapper_args__ = {"polymorphic_identity": "acetic_acid"}

    def __init__(self, **kwargs: Any) -> None:
        # Units are always g/L for acetic acid — override any caller-supplied value.
        kwargs["units"] = "g/L"
        super().__init__(**kwargs)
```

- [ ] **Step 5: Add AceticAcidSample to __all__**

Edit `src/modules/fermentation/src/domain/entities/samples/__init__.py`:

```python
"""
Sample Entities
-------------
Different types of measurements that can be taken during fermentation.

NOTE: This __init__.py intentionally does NOT import entities to avoid
SQLAlchemy registry conflicts during pytest discovery.
Import sample entities directly from their modules.
"""

__all__ = [
    'BaseSample',
    'SugarSample',
    'DensitySample',
    'CelsiusTemperatureSample',
    'AceticAcidSample',
]
```

- [ ] **Step 6: Run tests to confirm GREEN**

```
cd src/modules/fermentation
poetry run pytest tests/unit/domain/test_acetic_acid_sample.py -v
```

Expected: 6 passed.

- [ ] **Step 7: Run full fermentation suite — confirm no regressions**

```
cd src/modules/fermentation
poetry run pytest tests/ -q
```

Expected: all previously passing tests still pass.

- [ ] **Step 8: Commit**

```
git add src/modules/fermentation/src/domain/entities/samples/acetic_acid_sample.py \
        src/modules/fermentation/src/domain/entities/samples/__init__.py \
        src/modules/fermentation/src/domain/enums/sample_type.py \
        src/modules/fermentation/tests/unit/domain/test_acetic_acid_sample.py
git commit -m "feat(fermentation): add AceticAcidSample entity and SampleType.ACETIC_ACID

- AceticAcidSample extends BaseSample (STI, no migration needed)
- polymorphic_identity: acetic_acid, units: g/L (enforced in __init__)
- SampleType.ACETIC_ACID = 'acetic_acid' added to enum
- 6 tests added, all passing

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Task 2: ThresholdConfigService — TOML + dataclass (analysis_engine)

**Files:**
- Create: `src/modules/analysis_engine/config/thresholds.toml`
- Create: `src/modules/analysis_engine/config/thresholds_test.toml`
- Create: `src/modules/analysis_engine/src/service_component/services/threshold_config_service.py`
- Create: `src/modules/analysis_engine/tests/unit/service/test_threshold_config_service.py`
- Modify: `src/modules/analysis_engine/pyproject.toml`

- [ ] **Step 1: Add tomli dependency**

Edit `src/modules/analysis_engine/pyproject.toml` — add to `[tool.poetry.dependencies]`:

```toml
[tool.poetry.dependencies]
python = "^3.9"
sqlalchemy = "^2.0.20"
asyncpg = "^0.28.0"
greenlet = ">=3.0,<3.2.5"
pydantic = "^2.3.0"
psycopg2-binary = "^2.9.7"
loguru = "^0.7.0"
shared = {path = "../../shared", develop = true}
pytest-cov = "^4.1.0"
tomli = {version = "^2.0", python = "<3.11"}
```

Then install:

```
cd src/modules/analysis_engine
poetry install
```

Expected: `tomli` appears in `poetry.lock`.

- [ ] **Step 2: Write the failing tests**

Create `src/modules/analysis_engine/tests/unit/service/test_threshold_config_service.py`:

```python
"""
TDD tests for ThresholdConfigService.
RED: All tests fail — ThresholdConfigService does not exist yet.
"""
import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError


TESTS_DIR = Path(__file__).parent
CONFIG_DIR = Path(__file__).parents[4] / "config"
TEST_TOML_PATH = CONFIG_DIR / "thresholds_test.toml"


class TestVarietalThresholdsDataclass:
    def test_is_importable(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            VarietalThresholds,
        )
        assert VarietalThresholds is not None

    def test_is_frozen(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            VarietalThresholds,
        )
        t = VarietalThresholds(
            temperature_critical_min_celsius=23.9,
            temperature_critical_max_celsius=32.2,
            temperature_optimal_min_celsius=24.0,
            temperature_optimal_max_celsius=30.0,
            volatile_acidity_warning_in_grams_per_liter=0.6,
            volatile_acidity_critical_in_grams_per_liter=0.8,
            density_drop_max_percent_per_24_hours=15.0,
            hydrogen_sulfide_risk_max_temperature_celsius=18.0,
            hydrogen_sulfide_risk_critical_window_days=10.0,
            stuck_fermentation_min_density_change_points=1.0,
            stuck_fermentation_min_stall_duration_days=0.5,
        )
        with pytest.raises(FrozenInstanceError):
            t.temperature_critical_min_celsius = 99.0


class TestThresholdConfigServiceLoading:
    def test_loads_toml_and_returns_instance(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService, VarietalThresholds,
        )
        svc = ThresholdConfigService(config_path=TEST_TOML_PATH)
        result = svc.get_thresholds("Chardonnay")
        assert isinstance(result, VarietalThresholds)

    def test_red_varietal_cabernet_resolves_to_red_group(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService,
        )
        svc = ThresholdConfigService(config_path=TEST_TOML_PATH)
        result = svc.get_thresholds("Cabernet Sauvignon")
        # Test TOML has red.temperature_critical_min_celsius = 23.9
        assert result.temperature_critical_min_celsius == 23.9

    def test_white_varietal_chardonnay_resolves_to_white_group(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService,
        )
        svc = ThresholdConfigService(config_path=TEST_TOML_PATH)
        result = svc.get_thresholds("Chardonnay")
        # Test TOML has white.temperature_critical_min_celsius = 11.7
        assert result.temperature_critical_min_celsius == 11.7

    def test_unknown_varietal_falls_back_to_white_group(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService,
        )
        svc = ThresholdConfigService(config_path=TEST_TOML_PATH)
        result = svc.get_thresholds("UnknownGrape")
        assert result.temperature_critical_min_celsius == 11.7

    def test_all_red_varietals_resolve_to_red_group(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService,
        )
        svc = ThresholdConfigService(config_path=TEST_TOML_PATH)
        for variety in ["Cabernet Sauvignon", "Merlot", "Pinot Noir", "Zinfandel"]:
            result = svc.get_thresholds(variety)
            assert result.temperature_critical_min_celsius == 23.9, f"Failed for {variety}"

    def test_raises_on_missing_toml(self):
        from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
            ThresholdConfigService, ThresholdConfigError,
        )
        with pytest.raises(ThresholdConfigError):
            ThresholdConfigService(config_path=Path("/nonexistent/path/thresholds.toml"))
```

- [ ] **Step 3: Run tests to confirm RED**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_threshold_config_service.py -v
```

Expected: all fail with `ImportError: cannot import name 'ThresholdConfigService'`.

- [ ] **Step 4: Create thresholds.toml (production)**

Create directory and file `src/modules/analysis_engine/config/thresholds.toml`:

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
# Applied to all varietals — not varietal-specific thresholds
volatile_acidity_warning_in_grams_per_liter   = 0.6
volatile_acidity_critical_in_grams_per_liter  = 0.8
density_drop_max_percent_per_24_hours         = 15.0
hydrogen_sulfide_risk_max_temperature_celsius = 18.0
hydrogen_sulfide_risk_critical_window_days    = 10.0
stuck_fermentation_min_density_change_points  = 1.0
stuck_fermentation_min_stall_duration_days    = 0.5

[varietals.red]
# Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temperature_critical_min_celsius = 23.9   # 75°F — yeast death below
temperature_critical_max_celsius = 32.2   # 90°F — yeast death above
temperature_optimal_min_celsius  = 24.0
temperature_optimal_max_celsius  = 30.0

[varietals.white]
# All other varietals (whites, rosés) — also the fallback category
# Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
temperature_critical_min_celsius = 11.7   # 53°F
temperature_critical_max_celsius = 16.7   # 62°F
temperature_optimal_min_celsius  = 12.0
temperature_optimal_max_celsius  = 16.0
```

- [ ] **Step 5: Create thresholds_test.toml (predictable test values)**

Create `src/modules/analysis_engine/config/thresholds_test.toml`:

```toml
# Test-only threshold values — identical to production values.
# Having a separate file lets tests run without depending on production config path.

[defaults]
volatile_acidity_warning_in_grams_per_liter   = 0.6
volatile_acidity_critical_in_grams_per_liter  = 0.8
density_drop_max_percent_per_24_hours         = 15.0
hydrogen_sulfide_risk_max_temperature_celsius = 18.0
hydrogen_sulfide_risk_critical_window_days    = 10.0
stuck_fermentation_min_density_change_points  = 1.0
stuck_fermentation_min_stall_duration_days    = 0.5

[varietals.red]
temperature_critical_min_celsius = 23.9
temperature_critical_max_celsius = 32.2
temperature_optimal_min_celsius  = 24.0
temperature_optimal_max_celsius  = 30.0

[varietals.white]
temperature_critical_min_celsius = 11.7
temperature_critical_max_celsius = 16.7
temperature_optimal_min_celsius  = 12.0
temperature_optimal_max_celsius  = 16.0
```

- [ ] **Step 6: Create ThresholdConfigService**

Create `src/modules/analysis_engine/src/service_component/services/threshold_config_service.py`:

```python
"""
ThresholdConfigService — loads varietal anomaly detection thresholds from TOML.

Thresholds are resolved by varietal group (red / white) at runtime.
Loaded once at application startup via FastAPI lifespan; injected into
AnomalyDetectionService as a constructor dependency.

FUTURE — per-winery DB overrides (Option B):
    Change get_thresholds(variety) → get_thresholds(variety, winery_id=None).
    Implementation: query winery_varietal_thresholds table, fallback to TOML on miss.
    AnomalyDetectionService does NOT need to change — interface is identical.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]


class ThresholdConfigError(Exception):
    """Raised when thresholds.toml cannot be loaded or is malformed."""


@dataclass(frozen=True)
class VarietalThresholds:
    """Immutable threshold set for a varietal group.

    Field names are fully descriptive — no abbreviations — to avoid ambiguity
    when reading detection logic.
    """

    # Temperature limits
    temperature_critical_min_celsius: float
    temperature_critical_max_celsius: float
    temperature_optimal_min_celsius: float
    temperature_optimal_max_celsius: float
    # Volatile acidity
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


# Varietals that use red-wine temperature thresholds.
# All others default to the white/rosé group.
RED_VARIETALS: frozenset[str] = frozenset({
    "CABERNET SAUVIGNON",
    "MERLOT",
    "PINOT NOIR",
    "ZINFANDEL",
})

# Default config path — resolved relative to this file so it works regardless
# of the working directory the app is started from.
_DEFAULT_CONFIG_PATH = Path(__file__).parents[5] / "config" / "thresholds.toml"


class ThresholdConfigService:
    """
    Loads anomaly detection thresholds from a TOML config file.

    Usage:
        svc = ThresholdConfigService()                        # uses default path
        svc = ThresholdConfigService(config_path=some_path)  # override (tests)
        thresholds = svc.get_thresholds("Cabernet Sauvignon")
    """

    def __init__(self, config_path: Path | None = None) -> None:
        path = config_path or _DEFAULT_CONFIG_PATH
        try:
            with open(path, "rb") as f:
                self._config = tomllib.load(f)
        except FileNotFoundError as exc:
            raise ThresholdConfigError(
                f"Threshold config file not found: {path}"
            ) from exc
        except Exception as exc:
            raise ThresholdConfigError(
                f"Failed to load threshold config from {path}: {exc}"
            ) from exc

    def get_thresholds(self, variety: str) -> VarietalThresholds:
        """
        Return the VarietalThresholds for the given grape variety.

        Resolves to 'red' group for Cabernet Sauvignon, Merlot, Pinot Noir,
        Zinfandel; falls back to 'white' for everything else.
        """
        group = (
            "red"
            if variety.upper() in RED_VARIETALS
            else "white"
        )
        varietal_cfg = self._config["varietals"][group]
        defaults = self._config["defaults"]

        return VarietalThresholds(
            temperature_critical_min_celsius=varietal_cfg["temperature_critical_min_celsius"],
            temperature_critical_max_celsius=varietal_cfg["temperature_critical_max_celsius"],
            temperature_optimal_min_celsius=varietal_cfg["temperature_optimal_min_celsius"],
            temperature_optimal_max_celsius=varietal_cfg["temperature_optimal_max_celsius"],
            volatile_acidity_warning_in_grams_per_liter=defaults["volatile_acidity_warning_in_grams_per_liter"],
            volatile_acidity_critical_in_grams_per_liter=defaults["volatile_acidity_critical_in_grams_per_liter"],
            density_drop_max_percent_per_24_hours=defaults["density_drop_max_percent_per_24_hours"],
            hydrogen_sulfide_risk_max_temperature_celsius=defaults["hydrogen_sulfide_risk_max_temperature_celsius"],
            hydrogen_sulfide_risk_critical_window_days=defaults["hydrogen_sulfide_risk_critical_window_days"],
            stuck_fermentation_min_density_change_points=defaults["stuck_fermentation_min_density_change_points"],
            stuck_fermentation_min_stall_duration_days=defaults["stuck_fermentation_min_stall_duration_days"],
        )
```

- [ ] **Step 7: Run tests to confirm GREEN**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_threshold_config_service.py -v
```

Expected: 8 passed.

- [ ] **Step 8: Commit**

```
git add src/modules/analysis_engine/config/thresholds.toml \
        src/modules/analysis_engine/config/thresholds_test.toml \
        src/modules/analysis_engine/src/service_component/services/threshold_config_service.py \
        src/modules/analysis_engine/tests/unit/service/test_threshold_config_service.py \
        src/modules/analysis_engine/pyproject.toml \
        src/modules/analysis_engine/poetry.lock
git commit -m "feat(analysis_engine): add ThresholdConfigService with TOML-based varietal thresholds

- VarietalThresholds: frozen dataclass, fully descriptive field names
- ThresholdConfigService: loads thresholds.toml, resolves red/white group by variety
- RED_VARIETALS: Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel
- ThresholdConfigError raised on missing/malformed TOML
- tomli added as dependency for Python <3.11 TOML parsing
- 8 unit tests, all passing

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Task 3: Refactor AnomalyDetectionService to use ThresholdConfigService

**Files:**
- Modify: `src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py`
- Modify: `src/modules/analysis_engine/tests/conftest.py`
- Modify: `src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py`

- [ ] **Step 1: Add threshold_config fixture to conftest.py**

Edit `src/modules/analysis_engine/tests/conftest.py` — add at the end:

```python
from pathlib import Path

@pytest.fixture
def threshold_config():
    """
    Real ThresholdConfigService pointing at the test TOML.
    Use this in any test that instantiates AnomalyDetectionService.
    """
    from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
        ThresholdConfigService,
    )
    config_path = Path(__file__).parents[1] / "config" / "thresholds_test.toml"
    return ThresholdConfigService(config_path=config_path)
```

- [ ] **Step 2: Update service fixture AND existing test call sites (RED)**

Edit `src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py`:

**Update the `service` fixture:**
```python
@pytest.fixture
def service(mock_async_session, threshold_config):
    return AnomalyDetectionService(session=mock_async_session, threshold_config=threshold_config)
```

**Update every call site that passes thresholds explicitly** — the individual detection methods now accept a `thresholds` argument. The existing tests call these methods directly with 2 args (e.g. `service.detect_temperature_critical(temperature_celsius=33.0, variety="Cabernet Sauvignon")`). They need a third arg. Update each class as follows:

`TestTemperatureCriticalDetection` — add `thresholds` arg to each call:
```python
class TestTemperatureCriticalDetection:
    def test_detects_too_hot_red_variety(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Cabernet Sauvignon")
        result = service.detect_temperature_critical(temperature_celsius=33.0, variety="Cabernet Sauvignon", thresholds=thresholds)
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value
        assert result.severity == SeverityLevel.CRITICAL.value

    def test_detects_too_cold_red_variety(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Merlot")
        result = service.detect_temperature_critical(temperature_celsius=20.0, variety="Merlot", thresholds=thresholds)
        assert result is not None

    def test_no_anomaly_within_range_red(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Pinot Noir")
        result = service.detect_temperature_critical(temperature_celsius=28.0, variety="Pinot Noir", thresholds=thresholds)
        assert result is None

    def test_detects_too_hot_white_variety(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_temperature_critical(temperature_celsius=20.0, variety="Chardonnay", thresholds=thresholds)
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value

    def test_no_anomaly_within_range_white(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_temperature_critical(temperature_celsius=14.0, variety="Chardonnay", thresholds=thresholds)
        assert result is None
```

`TestTemperatureSuboptimalDetection`:
```python
class TestTemperatureSuboptimalDetection:
    def test_detects_suboptimal_cold_red(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Cabernet Sauvignon")
        result = service.detect_temperature_suboptimal(temperature_celsius=22.0, variety="Cabernet Sauvignon", thresholds=thresholds)
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_SUBOPTIMAL.value
        assert result.severity == SeverityLevel.WARNING.value

    def test_no_anomaly_in_optimal_range(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Merlot")
        result = service.detect_temperature_suboptimal(temperature_celsius=27.0, variety="Merlot", thresholds=thresholds)
        assert result is None
```

`TestDensityDropTooFast` — add `thresholds` arg:
```python
class TestDensityDropTooFast:
    def test_detects_fast_drop(self, service, threshold_config):
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        densities = [(base, 200.0), (base + timedelta(hours=24), 150.0)]
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_density_drop_too_fast(densities, thresholds)
        assert result is not None
        assert result.anomaly_type == AnomalyType.DENSITY_DROP_TOO_FAST.value
        assert result.severity == SeverityLevel.WARNING.value

    def test_no_anomaly_normal_drop(self, service, threshold_config):
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        densities = [(base, 100.0), (base + timedelta(hours=24), 95.0)]
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_density_drop_too_fast(densities, thresholds)
        assert result is None

    def test_no_anomaly_with_too_few_readings(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_density_drop_too_fast([], thresholds)
        assert result is None
```

`TestHydrogenSulfideRisk` — add `thresholds` arg:
```python
class TestHydrogenSulfideRisk:
    def test_detects_h2s_risk_cold_early(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=15.0, days_fermenting=5.0, thresholds=thresholds)
        assert result is not None
        assert result.anomaly_type == AnomalyType.HYDROGEN_SULFIDE_RISK.value

    def test_no_h2s_risk_warm_temperature(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=20.0, days_fermenting=5.0, thresholds=thresholds)
        assert result is None

    def test_no_h2s_risk_late_fermentation(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=15.0, days_fermenting=12.0, thresholds=thresholds)
        assert result is None
```

`TestStuckFermentationDetection` — add `thresholds` arg (async methods):
```python
class TestStuckFermentationDetection:
    @pytest.mark.asyncio
    async def test_detects_stuck_when_density_not_changing(self, service, threshold_config):
        densities = make_densities([50.0, 50.0, 50.0], gap_hours=12)
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = await service.detect_stuck_fermentation(
            current_density=50.0, previous_densities=densities, days_fermenting=5.0, thresholds=thresholds
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.STUCK_FERMENTATION.value
        assert result.severity == SeverityLevel.CRITICAL.value

    @pytest.mark.asyncio
    async def test_no_anomaly_when_density_decreasing_normally(self, service, threshold_config):
        densities = make_densities([100.0, 80.0, 60.0], gap_hours=12)
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = await service.detect_stuck_fermentation(
            current_density=60.0, previous_densities=densities, days_fermenting=3.0, thresholds=thresholds
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_anomaly_with_fewer_than_2_readings(self, service, threshold_config):
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = await service.detect_stuck_fermentation(
            current_density=50.0, previous_densities=[], days_fermenting=2.0, thresholds=thresholds
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_anomaly_when_density_at_dry_threshold(self, service, threshold_config):
        densities = make_densities([1.5, 1.5, 1.5], gap_hours=12)
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = await service.detect_stuck_fermentation(
            current_density=1.5, previous_densities=densities, days_fermenting=10.0, thresholds=thresholds
        )
        assert result is None
```

- [ ] **Step 3: Run existing anomaly detection tests to confirm RED**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_anomaly_detection_service.py -v
```

Expected: tests fail with `TypeError: AnomalyDetectionService.__init__() got an unexpected keyword argument 'threshold_config'`.

- [ ] **Step 4: Rewrite AnomalyDetectionService to inject ThresholdConfigService**

Replace the full content of `src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py`:

```python
"""
Anomaly Detection Service - Identify problems in fermentation.

Detects 8 types of anomalies using expert-validated thresholds from ADR-020.
Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)

Thresholds are loaded from config/thresholds.toml via ThresholdConfigService —
no magic numbers in this file.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore
from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
    ThresholdConfigService,
    VarietalThresholds,
)


class AnomalyDetectionService:
    """
    Service for detecting anomalies in fermentation data.

    Implements 8 anomaly types with expert-validated thresholds loaded from
    config/thresholds.toml via ThresholdConfigService.

    CRITICAL (Priority 1):
    - STUCK_FERMENTATION: Density static for 0.5-1 day, <1.0 pt change
    - TEMPERATURE_OUT_OF_RANGE_CRITICAL: outside absolute limits by varietal
    - VOLATILE_ACIDITY_HIGH: acetic acid > warning/critical threshold

    WARNING (Priority 2):
    - DENSITY_DROP_TOO_FAST: >15% in 24 hours
    - HYDROGEN_SULFIDE_RISK: cold temperature in critical window
    - TEMPERATURE_SUBOPTIMAL: off-spec but not critical

    INFO (Priority 3):
    - UNUSUAL_DURATION: outside 10-90 percentile vs historical
    - ATYPICAL_PATTERN: outside ±2σ band vs historical
    """

    def __init__(self, session: AsyncSession, threshold_config: ThresholdConfigService) -> None:
        self.session = session
        self.config = threshold_config

    async def detect_all_anomalies(
        self,
        fermentation_id: UUID,
        current_density: float,
        temperature_celsius: float,
        variety: str,
        days_fermenting: float,
        previous_densities: List[Tuple[datetime, float]],
        historical_avg_duration: Optional[float] = None,
        historical_densities_band: Optional[Dict] = None,
        volatile_acidity_in_grams_per_liter: Optional[float] = None,
    ) -> List[Anomaly]:
        """
        Run all anomaly detection algorithms.

        Args:
            fermentation_id: Current fermentation ID
            current_density: Current density reading (g/L)
            temperature_celsius: Current temperature
            variety: Grape variety (determines temperature thresholds)
            days_fermenting: Days since fermentation start
            previous_densities: List of (timestamp, density) tuples
            historical_avg_duration: Average duration from similar fermentations
            historical_densities_band: Statistical band (mean, stdev)
            volatile_acidity_in_grams_per_liter: Acetic acid reading in g/L (optional)

        Returns:
            List of detected Anomaly objects (empty if no issues)
        """
        thresholds = self.config.get_thresholds(variety)
        anomalies = []

        stuck = await self.detect_stuck_fermentation(
            current_density,
            previous_densities,
            days_fermenting,
            thresholds,
        )
        if stuck:
            anomalies.append(stuck)

        temp_critical = self.detect_temperature_critical(temperature_celsius, variety, thresholds)
        if temp_critical:
            anomalies.append(temp_critical)

        temp_suboptimal = self.detect_temperature_suboptimal(temperature_celsius, variety, thresholds)
        if temp_suboptimal and not temp_critical:
            anomalies.append(temp_suboptimal)

        fast_drop = self.detect_density_drop_too_fast(previous_densities, thresholds)
        if fast_drop:
            anomalies.append(fast_drop)

        h2s_risk = self.detect_hydrogen_sulfide_risk(temperature_celsius, days_fermenting, thresholds)
        if h2s_risk:
            anomalies.append(h2s_risk)

        if volatile_acidity_in_grams_per_liter is not None:
            va = self.detect_volatile_acidity(volatile_acidity_in_grams_per_liter, thresholds)
            if va:
                anomalies.append(va)

        if historical_avg_duration:
            unusual = self.detect_unusual_duration(days_fermenting, historical_avg_duration)
            if unusual:
                anomalies.append(unusual)

        if historical_densities_band:
            atypical = self.detect_atypical_pattern(current_density, historical_densities_band)
            if atypical:
                anomalies.append(atypical)

        return anomalies

    async def detect_stuck_fermentation(
        self,
        current_density: float,
        previous_densities: List[Tuple[datetime, float]],
        days_fermenting: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect fermentation stalling before reaching dry wine (<2 g/L)."""
        if not previous_densities or len(previous_densities) < 2:
            return None

        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        recent_start_idx = max(0, len(sorted_densities) - 3)
        recent_readings = sorted_densities[recent_start_idx:]
        if len(recent_readings) < 2:
            return None

        oldest_recent = recent_readings[0][1]
        newest_recent = recent_readings[-1][1]
        density_change = abs(newest_recent - oldest_recent)
        time_span = (recent_readings[-1][0] - recent_readings[0][0]).total_seconds() / 86400

        min_change = thresholds.stuck_fermentation_min_density_change_points
        min_stall = thresholds.stuck_fermentation_min_stall_duration_days
        is_stuck = density_change < min_change and time_span > min_stall and current_density > 2.0

        if not is_stuck:
            return None

        deviation = DeviationScore(
            deviation=density_change,
            threshold=min_change,
            magnitude="LOW",
            details={
                "time_span_days": round(time_span, 2),
                "density_change_points": round(density_change, 2),
                "current_density": current_density,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description=(
                f"Fermentación estancada: densidad sin cambio por {time_span:.1f} días. "
                f"Cambio: {density_change:.2f} puntos, umbral: {min_change}"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_temperature_critical(
        self,
        temperature_celsius: float,
        variety: str,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect temperature outside absolute critical limits."""
        min_temp = thresholds.temperature_critical_min_celsius
        max_temp = thresholds.temperature_critical_max_celsius
        is_critical = temperature_celsius < min_temp or temperature_celsius > max_temp
        if not is_critical:
            return None

        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=min_temp if temperature_celsius < min_temp else max_temp,
            magnitude="HIGH",
            details={
                "min_critical": min_temp,
                "max_critical": max_temp,
                "current_temp": round(temperature_celsius, 1),
            },
        )
        direction = "too cold" if temperature_celsius < min_temp else "too hot"
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value,
            severity=SeverityLevel.CRITICAL.value,
            description=(
                f"Temperatura fuera de límites críticos ({direction}): "
                f"{temperature_celsius:.1f}°C. Rango: {min_temp}-{max_temp}°C"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_temperature_suboptimal(
        self,
        temperature_celsius: float,
        variety: str,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect temperature outside optimal (but not critical) range."""
        min_opt = thresholds.temperature_optimal_min_celsius
        max_opt = thresholds.temperature_optimal_max_celsius
        is_suboptimal = temperature_celsius < min_opt or temperature_celsius > max_opt
        if not is_suboptimal:
            return None

        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=(min_opt + max_opt) / 2,
            magnitude="MEDIUM",
            details={
                "min_optimal": min_opt,
                "max_optimal": max_opt,
                "current_temp": round(temperature_celsius, 1),
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.TEMPERATURE_SUBOPTIMAL.value,
            severity=SeverityLevel.WARNING.value,
            description=(
                f"Temperatura subóptima: {temperature_celsius:.1f}°C. "
                f"Rango óptimo: {min_opt}-{max_opt}°C"
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_density_drop_too_fast(
        self,
        previous_densities: List[Tuple[datetime, float]],
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect fermentation proceeding too fast."""
        if not previous_densities or len(previous_densities) < 2:
            return None

        sorted_densities = sorted(previous_densities, key=lambda x: x[0])
        max_drop_pct = thresholds.density_drop_max_percent_per_24_hours

        for i in range(len(sorted_densities) - 1):
            time_diff = (sorted_densities[i + 1][0] - sorted_densities[i][0]).total_seconds() / 3600
            if 20 <= time_diff <= 28:
                density_1 = sorted_densities[i][1]
                density_2 = sorted_densities[i + 1][1]
                percent_change = abs(density_2 - density_1) / max(density_1, 0.1) * 100
                if percent_change > max_drop_pct:
                    deviation = DeviationScore(
                        deviation=percent_change,
                        threshold=max_drop_pct,
                        magnitude="MEDIUM",
                        details={
                            "time_span_hours": round(time_diff, 1),
                            "percent_change": round(percent_change, 1),
                            "density_start": round(density_1, 2),
                            "density_end": round(density_2, 2),
                        },
                    )
                    return Anomaly(
                        anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
                        severity=SeverityLevel.WARNING.value,
                        description=(
                            f"Caída de densidad demasiado rápida: {percent_change:.1f}% en 24h. "
                            f"Umbral: {max_drop_pct}%"
                        ),
                        deviation_score=deviation.to_dict(),
                        is_resolved=False,
                    )
        return None

    def detect_hydrogen_sulfide_risk(
        self,
        temperature_celsius: float,
        days_fermenting: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """Detect conditions favorable for H₂S development."""
        max_temp = thresholds.hydrogen_sulfide_risk_max_temperature_celsius
        critical_window = thresholds.hydrogen_sulfide_risk_critical_window_days
        is_risk = temperature_celsius < max_temp and days_fermenting < critical_window

        if not is_risk:
            return None

        deviation = DeviationScore(
            deviation=temperature_celsius,
            threshold=max_temp,
            magnitude="MEDIUM",
            details={
                "critical_period_days": min(days_fermenting, critical_window),
                "current_temp": round(temperature_celsius, 1),
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.HYDROGEN_SULFIDE_RISK.value,
            severity=SeverityLevel.WARNING.value,
            description=(
                f"Riesgo de H₂S: temperatura baja ({temperature_celsius:.1f}°C) "
                f"en fase crítica de fermentación ({days_fermenting:.1f} días). "
                f"Considerar aireación."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_volatile_acidity(
        self,
        volatile_acidity_in_grams_per_liter: float,
        thresholds: VarietalThresholds,
    ) -> Optional[Anomaly]:
        """
        Detect elevated volatile acidity (acetic acid).

        Thresholds (from config/thresholds.toml):
          Warning:  > volatile_acidity_warning_in_grams_per_liter  (default 0.6 g/L)
          Critical: > volatile_acidity_critical_in_grams_per_liter (default 0.8 g/L)

        Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery)
        """
        critical = thresholds.volatile_acidity_critical_in_grams_per_liter
        warning = thresholds.volatile_acidity_warning_in_grams_per_liter

        if volatile_acidity_in_grams_per_liter > critical:
            severity = SeverityLevel.CRITICAL
        elif volatile_acidity_in_grams_per_liter > warning:
            severity = SeverityLevel.WARNING
        else:
            return None

        deviation = DeviationScore(
            deviation=volatile_acidity_in_grams_per_liter,
            threshold=warning,
            magnitude="HIGH" if severity == SeverityLevel.CRITICAL else "MEDIUM",
            details={
                "current_g_l": round(volatile_acidity_in_grams_per_liter, 3),
                "warning_threshold_g_l": warning,
                "critical_threshold_g_l": critical,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.VOLATILE_ACIDITY_HIGH.value,
            severity=severity.value,
            description=(
                f"Acidez volátil elevada: {volatile_acidity_in_grams_per_liter:.3f} g/L "
                f"(umbral crítico: {critical} g/L). Riesgo de acetificación."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_unusual_duration(
        self,
        days_fermenting: float,
        historical_avg_duration: float,
    ) -> Optional[Anomaly]:
        """Detect fermentation duration outside typical range."""
        if not historical_avg_duration or historical_avg_duration <= 0:
            return None

        tolerance = 1.5
        too_long = days_fermenting > historical_avg_duration + tolerance
        too_short = (
            days_fermenting >= historical_avg_duration * 0.6
            and days_fermenting < historical_avg_duration - tolerance
        )
        if not (too_long or too_short):
            return None

        deviation = DeviationScore(
            deviation=days_fermenting,
            threshold=historical_avg_duration,
            magnitude="LOW",
            details={
                "current_days": round(days_fermenting, 1),
                "historical_avg_days": round(historical_avg_duration, 1),
                "tolerance_days": tolerance,
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description=(
                f"Duración atípica: {days_fermenting:.1f} días vs histórico "
                f"{historical_avg_duration:.1f} días. Informativo - observar evolución."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )

    def detect_atypical_pattern(
        self,
        current_density: float,
        historical_densities_band: Dict,
    ) -> Optional[Anomaly]:
        """Detect density reading outside ±2σ of historical pattern."""
        if not historical_densities_band or "mean" not in historical_densities_band:
            return None

        mean = historical_densities_band["mean"]
        stdev = historical_densities_band.get("stdev", 0)
        if stdev <= 0:
            return None

        z_score = abs(current_density - mean) / stdev
        if z_score <= 2.0:
            return None

        deviation = DeviationScore(
            deviation=current_density,
            threshold=mean,
            magnitude="MEDIUM",
            details={
                "z_score": round(z_score, 2),
                "current_density": round(current_density, 2),
                "historical_mean": round(mean, 2),
                "standard_deviations": round(stdev, 2),
            },
        )
        return Anomaly(
            anomaly_type=AnomalyType.ATYPICAL_PATTERN.value,
            severity=SeverityLevel.INFO.value,
            description=(
                f"Patrón atípico: densidad {current_density:.2f} está fuera de banda histórica "
                f"(z-score {z_score:.2f}). Investigar evolución."
            ),
            deviation_score=deviation.to_dict(),
            is_resolved=False,
        )
```

- [ ] **Step 5: Run anomaly detection tests to confirm GREEN (excluding volatile acidity skips)**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_anomaly_detection_service.py -v
```

Expected: all previously-passing tests pass, 3 still skipped (volatile acidity — we remove those in Task 4).

- [ ] **Step 6: Commit**

```
git add src/modules/analysis_engine/src/service_component/services/anomaly_detection_service.py \
        src/modules/analysis_engine/tests/conftest.py \
        src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py
git commit -m "refactor(analysis_engine): inject ThresholdConfigService into AnomalyDetectionService

- All hardcoded threshold literals replaced with VarietalThresholds fields
- detect_volatile_acidity() implemented (still skipped in tests — Task 4)
- All detection method signatures updated to accept thresholds parameter
- detect_all_anomalies() accepts optional volatile_acidity_in_grams_per_liter param
- threshold_config fixture added to conftest.py

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Task 4: Unlock the 3 volatile acidity tests

**Files:**
- Modify: `src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py`

- [ ] **Step 1: Remove @pytest.mark.skip and update test signatures (RED)**

In `src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py`, replace the entire `TestVolatileAcidityDetection` class:

```python
class TestVolatileAcidityDetection:
    """Tests for volatile acidity (acetic acid) detection via AceticAcidSample."""

    def test_detects_critical_anomaly_when_above_critical_threshold(self, service, threshold_config):
        # 1.4 g/L > 0.8 g/L critical threshold → CRITICAL
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_volatile_acidity(
            volatile_acidity_in_grams_per_liter=1.4,
            thresholds=thresholds,
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.VOLATILE_ACIDITY_HIGH.value
        assert result.severity == SeverityLevel.CRITICAL.value

    def test_detects_warning_anomaly_when_between_warning_and_critical(self, service, threshold_config):
        # 0.7 g/L is between 0.6 (warning) and 0.8 (critical) → WARNING
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_volatile_acidity(
            volatile_acidity_in_grams_per_liter=0.7,
            thresholds=thresholds,
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.VOLATILE_ACIDITY_HIGH.value
        assert result.severity == SeverityLevel.WARNING.value

    def test_no_anomaly_when_below_warning_threshold(self, service, threshold_config):
        # 0.4 g/L < 0.6 g/L warning threshold → no anomaly
        thresholds = threshold_config.get_thresholds("Chardonnay")
        result = service.detect_volatile_acidity(
            volatile_acidity_in_grams_per_liter=0.4,
            thresholds=thresholds,
        )
        assert result is None
```

- [ ] **Step 2: Run the 3 tests to confirm they are now RED (not skipped)**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_anomaly_detection_service.py::TestVolatileAcidityDetection -v
```

Expected: 3 FAILED (not skipped) — method exists, but test was skipped before. If they pass directly, that's GREEN — move on.

- [ ] **Step 3: Run full anomaly detection suite to confirm GREEN**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_anomaly_detection_service.py -v
```

Expected: all 23 tests pass, 0 skipped.

- [ ] **Step 4: Run full analysis_engine test suite**

```
cd src/modules/analysis_engine
poetry run pytest tests/ -q
```

Expected: 201+ passed, skipped count drops by 3 (from 7 to 4). The remaining 4 skips are the cross-module integration tests (correctly covered by `tests/integration/`).

- [ ] **Step 5: Commit**

```
git add src/modules/analysis_engine/tests/unit/service/test_anomaly_detection_service.py
git commit -m "test(analysis_engine): unlock 3 volatile acidity tests — now pass with AceticAcidSample

- Remove @pytest.mark.skip from TestVolatileAcidityDetection (3 tests)
- Update test signatures to use thresholds parameter
- All 3 tests now pass: CRITICAL (>0.8 g/L), WARNING (0.6-0.8 g/L), no anomaly (<0.6 g/L)
- analysis_engine: 204 passed, 4 skipped (cross-module integration covered separately)

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Task 5: Wire ThresholdConfigService into dependencies.py and orchestrator

**Files:**
- Modify: `src/modules/analysis_engine/src/service_component/services/analysis_orchestrator_service.py`
- Modify: `src/modules/analysis_engine/src/api/dependencies.py`

- [ ] **Step 1: Update AnalysisOrchestratorService to pass threshold_config to AnomalyDetectionService**

In `src/modules/analysis_engine/src/service_component/services/analysis_orchestrator_service.py`, update `__init__` and add the import:

```python
from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
    ThresholdConfigService,
)

class AnalysisOrchestratorService:
    def __init__(self, session: AsyncSession, threshold_config: ThresholdConfigService) -> None:
        self.session = session
        self.comparison = ComparisonService(session)
        self.anomaly_detection = AnomalyDetectionService(session, threshold_config)
        self.recommendation = RecommendationService(session)
        self.protocol_integration = ProtocolAnalysisIntegrationService()
```

- [ ] **Step 2: Run orchestrator tests to confirm they still pass**

```
cd src/modules/analysis_engine
poetry run pytest tests/unit/service/test_analysis_orchestrator_service.py -v
```

Expected: all previously-passing tests still pass (they mock at session level and don't construct `AnomalyDetectionService` directly). If any fail with `TypeError: __init__() missing ... threshold_config`, update the orchestrator instantiation in those tests to pass `MagicMock()` for `threshold_config`.

- [ ] **Step 3: Update dependencies.py to instantiate ThresholdConfigService as a singleton**

Replace the full content of `src/modules/analysis_engine/src/api/dependencies.py`:

```python
"""
FastAPI dependencies for Analysis Engine API Layer.

ThresholdConfigService is instantiated once as a module-level singleton — it
loads thresholds.toml once at import time and is reused for every request.
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.fastapi_session import get_db_session
from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import (
    AnalysisOrchestratorService,
)
from src.modules.analysis_engine.src.service_component.services.threshold_config_service import (
    ThresholdConfigService,
)
from src.modules.analysis_engine.src.repository_component.repositories.recommendation_repository import (
    RecommendationRepository,
)
from src.modules.analysis_engine.src.repository_component.repositories.protocol_advisory_repository import (
    ProtocolAdvisoryRepository,
)

# Loaded once at startup — thresholds.toml read once, reused for every request.
_threshold_config = ThresholdConfigService()


async def get_analysis_orchestrator(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> AnalysisOrchestratorService:
    """Provide an AnalysisOrchestratorService with the current DB session."""
    return AnalysisOrchestratorService(session, _threshold_config)


async def get_recommendation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> RecommendationRepository:
    """Provide a RecommendationRepository connected to the current DB session."""
    from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager
    session_manager = FastAPISessionManager(session)
    return RecommendationRepository(session_manager)


async def get_protocol_advisory_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> ProtocolAdvisoryRepository:
    """Provide a ProtocolAdvisoryRepository connected to the current DB session."""
    from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager
    session_manager = FastAPISessionManager(session)
    return ProtocolAdvisoryRepository(session_manager)
```

- [ ] **Step 4: Run full analysis_engine test suite — confirm no regressions**

```
cd src/modules/analysis_engine
poetry run pytest tests/ -q
```

Expected: 204+ passed, 4 skipped.

- [ ] **Step 5: Commit**

```
git add src/modules/analysis_engine/src/service_component/services/analysis_orchestrator_service.py \
        src/modules/analysis_engine/src/api/dependencies.py
git commit -m "feat(analysis_engine): wire ThresholdConfigService through orchestrator and dependencies

- AnalysisOrchestratorService.__init__ now accepts threshold_config parameter
- dependencies.py instantiates ThresholdConfigService once as module-level singleton
- Full test suite: 204+ passed, 4 skipped

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Task 6: Update .ai-context documentation

**Files:**
- Modify: `src/modules/fermentation/src/domain/.ai-context/component-context.md`
- Modify: `src/modules/analysis_engine/src/service_component/.ai-context/component-context.md`

- [ ] **Step 1: Update fermentation domain context**

In `src/modules/fermentation/src/domain/.ai-context/component-context.md`, add to the Entities section:

```markdown
## Sample types (STI — single table inheritance on `samples` table)

All sample subclasses extend `BaseSample`. No migration needed to add a new type.

| Class | polymorphic_identity | units | Measures |
|-------|---------------------|-------|----------|
| `SugarSample` | `sugar` | brix | Sugar content |
| `DensitySample` | `density` | specific_gravity | Density |
| `CelsiusTemperatureSample` | `temperature` | °C | Temperature |
| `AceticAcidSample` | `acetic_acid` | g/L | Volatile acidity (acetic acid) |

**Adding a new sample type:**
1. Create `src/domain/entities/samples/<name>_sample.py` extending `BaseSample`
2. Set `polymorphic_identity` in `__mapper_args__` and default `units` in `__init__`
3. Add enum value to `SampleType`
4. Add class name to `__all__` in `samples/__init__.py`

**Planned (add when frontend + schema ready):**
- `LacticAcidSample` (g/L) — malolactic fermentation monitoring
- `SulfurDioxideSample` (mg/L) — SO₂ preservation monitoring
```

- [ ] **Step 2: Update analysis_engine service component context**

In `src/modules/analysis_engine/src/service_component/.ai-context/component-context.md`, add `ThresholdConfigService` to the services table and append:

```markdown
## ThresholdConfigService

| | |
|---|---|
| **File** | `src/service_component/services/threshold_config_service.py` |
| **Config** | `config/thresholds.toml` (production), `config/thresholds_test.toml` (tests) |
| **Responsibility** | Loads anomaly detection thresholds from TOML; resolves by varietal group |

**Varietal groups:**
- `red`: Cabernet Sauvignon, Merlot, Pinot Noir, Zinfandel — all others fall back to `white`

**VarietalThresholds fields** (frozen dataclass, no abbreviations):
- `temperature_critical_min_celsius`, `temperature_critical_max_celsius`
- `temperature_optimal_min_celsius`, `temperature_optimal_max_celsius`
- `volatile_acidity_warning_in_grams_per_liter`, `volatile_acidity_critical_in_grams_per_liter`
- `density_drop_max_percent_per_24_hours`
- `hydrogen_sulfide_risk_max_temperature_celsius`, `hydrogen_sulfide_risk_critical_window_days`
- `stuck_fermentation_min_density_change_points`, `stuck_fermentation_min_stall_duration_days`

**Migration path to per-winery DB overrides (Option B — when first client onboarded):**
1. Add table `winery_varietal_thresholds(id, winery_id UUID, varietal_group VARCHAR, key VARCHAR, value FLOAT)`
2. Change signature: `get_thresholds(variety)` → `get_thresholds(variety, winery_id=None)`
3. Query DB for winery row, fallback to TOML on miss
4. `AnomalyDetectionService` does NOT change — interface is identical
5. Seed DB from `thresholds.toml` values on first winery setup
```

- [ ] **Step 3: Commit**

```
git add src/modules/fermentation/src/domain/.ai-context/component-context.md \
        src/modules/analysis_engine/src/service_component/.ai-context/component-context.md
git commit -m "docs: update ai-context for AceticAcidSample and ThresholdConfigService

- fermentation domain context: add STI sample type table + extension guide
- analysis_engine service context: document ThresholdConfigService, VarietalThresholds fields,
  Option B migration path to per-winery DB overrides

Co-Authored-By: Claude Sonnet 4 <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Run both module test suites end-to-end**

```
cd src/modules/fermentation
poetry run pytest tests/ -q

cd ../analysis_engine
poetry run pytest tests/ -q
```

Expected:
- `fermentation`: all previously passing tests + 6 new `test_acetic_acid_sample.py` tests pass
- `analysis_engine`: 204+ passed, 4 skipped (cross-module integration covered by `tests/integration/`)

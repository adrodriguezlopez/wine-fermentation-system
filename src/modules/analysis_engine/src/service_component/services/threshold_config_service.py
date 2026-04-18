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
# File is at: src/modules/analysis_engine/src/service_component/services/threshold_config_service.py
# parents[3] = src/modules/analysis_engine/
_DEFAULT_CONFIG_PATH = Path(__file__).parents[3] / "config" / "thresholds.toml"


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

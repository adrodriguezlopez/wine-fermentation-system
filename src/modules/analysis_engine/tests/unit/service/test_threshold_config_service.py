"""
TDD tests for ThresholdConfigService.
RED: All tests fail — ThresholdConfigService does not exist yet.
"""
import pytest
from pathlib import Path
from dataclasses import FrozenInstanceError


TESTS_DIR = Path(__file__).parent
CONFIG_DIR = Path(__file__).parents[3] / "config"
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

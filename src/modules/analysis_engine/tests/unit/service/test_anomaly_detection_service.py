"""
Tests for AnomalyDetectionService.
"""
import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.anomaly_detection_service import (
    AnomalyDetectionService,
)
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


def make_densities(values, base_time=None, gap_hours=24):
    """Helper: build list of (datetime, float) from a list of density values."""
    if base_time is None:
        base_time = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return [(base_time + timedelta(hours=i * gap_hours), v) for i, v in enumerate(values)]


@pytest.fixture
def service(mock_async_session):
    return AnomalyDetectionService(session=mock_async_session)


class TestStuckFermentationDetection:
    @pytest.mark.asyncio
    async def test_detects_stuck_when_density_not_changing(self, service):
        # Same density across 3 readings spanning >0.5 days
        densities = make_densities([50.0, 50.0, 50.0], gap_hours=12)
        result = await service.detect_stuck_fermentation(
            current_density=50.0,
            previous_densities=densities,
            days_fermenting=5.0,
        )
        assert result is not None
        assert result.anomaly_type == AnomalyType.STUCK_FERMENTATION.value
        assert result.severity == SeverityLevel.CRITICAL.value

    @pytest.mark.asyncio
    async def test_no_anomaly_when_density_decreasing_normally(self, service):
        densities = make_densities([100.0, 80.0, 60.0], gap_hours=12)
        result = await service.detect_stuck_fermentation(
            current_density=60.0,
            previous_densities=densities,
            days_fermenting=3.0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_anomaly_with_fewer_than_2_readings(self, service):
        result = await service.detect_stuck_fermentation(
            current_density=50.0,
            previous_densities=[],
            days_fermenting=2.0,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_no_anomaly_when_density_at_dry_threshold(self, service):
        # density <= 2.0 means fermentation finished — no stuck anomaly
        densities = make_densities([1.5, 1.5, 1.5], gap_hours=12)
        result = await service.detect_stuck_fermentation(
            current_density=1.5,
            previous_densities=densities,
            days_fermenting=10.0,
        )
        assert result is None


class TestTemperatureCriticalDetection:
    def test_detects_too_hot_red_variety(self, service):
        result = service.detect_temperature_critical(temperature_celsius=33.0, variety="Cabernet Sauvignon")
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value
        assert result.severity == SeverityLevel.CRITICAL.value

    def test_detects_too_cold_red_variety(self, service):
        result = service.detect_temperature_critical(temperature_celsius=20.0, variety="Merlot")
        assert result is not None

    def test_no_anomaly_within_range_red(self, service):
        result = service.detect_temperature_critical(temperature_celsius=28.0, variety="Pinot Noir")
        assert result is None

    def test_detects_too_hot_white_variety(self, service):
        result = service.detect_temperature_critical(temperature_celsius=20.0, variety="Chardonnay")
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value

    def test_no_anomaly_within_range_white(self, service):
        result = service.detect_temperature_critical(temperature_celsius=14.0, variety="Chardonnay")
        assert result is None


class TestTemperatureSuboptimalDetection:
    def test_detects_suboptimal_cold_red(self, service):
        result = service.detect_temperature_suboptimal(temperature_celsius=22.0, variety="Cabernet Sauvignon")
        assert result is not None
        assert result.anomaly_type == AnomalyType.TEMPERATURE_SUBOPTIMAL.value
        assert result.severity == SeverityLevel.WARNING.value

    def test_no_anomaly_in_optimal_range(self, service):
        result = service.detect_temperature_suboptimal(temperature_celsius=27.0, variety="Merlot")
        assert result is None


class TestDensityDropTooFast:
    def test_detects_fast_drop(self, service):
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        densities = [(base, 200.0), (base + timedelta(hours=24), 150.0)]
        result = service.detect_density_drop_too_fast(densities)
        assert result is not None
        assert result.anomaly_type == AnomalyType.DENSITY_DROP_TOO_FAST.value
        assert result.severity == SeverityLevel.WARNING.value

    def test_no_anomaly_normal_drop(self, service):
        base = datetime(2025, 1, 1, tzinfo=timezone.utc)
        densities = [(base, 100.0), (base + timedelta(hours=24), 95.0)]
        result = service.detect_density_drop_too_fast(densities)
        assert result is None

    def test_no_anomaly_with_too_few_readings(self, service):
        result = service.detect_density_drop_too_fast([])
        assert result is None


class TestHydrogenSulfideRisk:
    def test_detects_h2s_risk_cold_early(self, service):
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=15.0, days_fermenting=5.0)
        assert result is not None
        assert result.anomaly_type == AnomalyType.HYDROGEN_SULFIDE_RISK.value

    def test_no_h2s_risk_warm_temperature(self, service):
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=20.0, days_fermenting=5.0)
        assert result is None

    def test_no_h2s_risk_late_fermentation(self, service):
        result = service.detect_hydrogen_sulfide_risk(temperature_celsius=15.0, days_fermenting=12.0)
        assert result is None


class TestUnusualDuration:
    def test_detects_too_long(self, service):
        result = service.detect_unusual_duration(days_fermenting=20.0, historical_avg_duration=10.0)
        assert result is not None
        assert result.anomaly_type == AnomalyType.UNUSUAL_DURATION.value
        assert result.severity == SeverityLevel.INFO.value

    def test_no_anomaly_within_normal_range(self, service):
        result = service.detect_unusual_duration(days_fermenting=10.5, historical_avg_duration=10.0)
        assert result is None

    def test_no_anomaly_when_no_historical_data(self, service):
        result = service.detect_unusual_duration(days_fermenting=10.0, historical_avg_duration=None)
        assert result is None


class TestVolatileAcidityDetection:
    """
    Tests for volatile acidity detection.

    NOTE: detect_volatile_acidity() is marked as TODO in the service
    (requires chemical data not yet in schema — see AnomalyDetectionService source).
    These tests are skipped until the method is implemented and are here to
    document the expected contract per ADR-020 / spec requirements.
    """

    @pytest.mark.skip(reason="detect_volatile_acidity not yet implemented in service (TODO)")
    def test_detects_anomaly_when_volatile_acidity_high(self, service):
        result = service.detect_volatile_acidity(volatile_acidity_g_l=1.4)
        assert result is not None
        assert result.anomaly_type == AnomalyType.VOLATILE_ACIDITY_HIGH.value
        assert result.severity == SeverityLevel.CRITICAL.value

    @pytest.mark.skip(reason="detect_volatile_acidity not yet implemented in service (TODO)")
    def test_no_anomaly_when_volatile_acidity_within_normal_range(self, service):
        result = service.detect_volatile_acidity(volatile_acidity_g_l=0.4)
        assert result is None

    @pytest.mark.skip(reason="detect_volatile_acidity not yet implemented in service (TODO)")
    def test_returns_correct_anomaly_type_and_critical_severity(self, service):
        result = service.detect_volatile_acidity(volatile_acidity_g_l=1.2)
        assert result is not None
        assert result.anomaly_type == AnomalyType.VOLATILE_ACIDITY_HIGH.value
        assert result.severity == SeverityLevel.CRITICAL.value


class TestAtypicalPattern:
    def test_detects_outside_2_sigma_band(self, service):
        band = {"mean": 100.0, "stdev": 5.0}
        # z_score = |88-100|/5 = 2.4 > 2.0 → should detect
        result = service.detect_atypical_pattern(current_density=88.0, historical_densities_band=band)
        assert result is not None
        assert result.anomaly_type == AnomalyType.ATYPICAL_PATTERN.value

    def test_no_anomaly_within_band(self, service):
        band = {"mean": 100.0, "stdev": 5.0}
        result = service.detect_atypical_pattern(current_density=101.0, historical_densities_band=band)
        assert result is None

    def test_no_anomaly_when_band_missing(self, service):
        result = service.detect_atypical_pattern(current_density=100.0, historical_densities_band=None)
        assert result is None

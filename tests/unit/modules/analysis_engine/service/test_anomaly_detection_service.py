"""Tests for Anomaly Detection Service."""
import pytest
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.modules.analysis_engine.src.service_component.services.anomaly_detection_service import AnomalyDetectionService
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


@pytest.fixture
def anomaly_service(session: AsyncSession):
    """Create an Anomaly Detection Service instance."""
    return AnomalyDetectionService(session)


class TestStuckFermentationDetection:
    """Tests for stuck fermentation detection."""
    
    @pytest.mark.asyncio
    async def test_no_stuck_with_active_fermentation(self, anomaly_service: AnomalyDetectionService):
        """Active fermentation should not be flagged."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(days=1), 1010.0),
            (now, 1005.0),
        ]
        
        anomaly = await anomaly_service.detect_stuck_fermentation(
            current_density=1005.0,
            previous_densities=previous_densities,
            days_fermenting=1.0
        )
        
        assert anomaly is None
    
    @pytest.mark.asyncio
    async def test_stuck_fermentation_detected(self, anomaly_service: AnomalyDetectionService):
        """Fermentation with no density change for >0.5 days should be flagged."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(hours=13), 1005.0),
            (now, 1005.0),  # No change in 13 hours
        ]
        
        anomaly = await anomaly_service.detect_stuck_fermentation(
            current_density=1005.0,
            previous_densities=previous_densities,
            days_fermenting=2.0
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.STUCK_FERMENTATION.value
        assert anomaly.severity == SeverityLevel.CRITICAL.value


class TestTemperatureCriticalDetection:
    """Tests for critical temperature detection."""
    
    def test_red_wine_too_cold(self, anomaly_service: AnomalyDetectionService):
        """Red wine below 23.9°C should be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=23.0,
            variety="Cabernet Sauvignon"
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.value
        assert anomaly.severity == SeverityLevel.CRITICAL.value
    
    def test_red_wine_too_hot(self, anomaly_service: AnomalyDetectionService):
        """Red wine above 32.2°C should be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=33.0,
            variety="Pinot Noir"
        )
        
        assert anomaly is not None
        assert anomaly.severity == SeverityLevel.CRITICAL.value
    
    def test_red_wine_in_range(self, anomaly_service: AnomalyDetectionService):
        """Red wine 24-32°C should not be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=28.0,
            variety="Merlot"
        )
        
        assert anomaly is None
    
    def test_white_wine_too_cold(self, anomaly_service: AnomalyDetectionService):
        """White wine below 11.7°C should be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=10.0,
            variety="Sauvignon Blanc"
        )
        
        assert anomaly is not None
        assert anomaly.severity == SeverityLevel.CRITICAL.value
    
    def test_white_wine_too_hot(self, anomaly_service: AnomalyDetectionService):
        """White wine above 16.7°C should be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=18.0,
            variety="Chardonnay"
        )
        
        assert anomaly is not None
        assert anomaly.severity == SeverityLevel.CRITICAL.value
    
    def test_white_wine_in_range(self, anomaly_service: AnomalyDetectionService):
        """White wine 11.7-16.7°C should not be critical."""
        anomaly = anomaly_service.detect_temperature_critical(
            temperature_celsius=14.0,
            variety="Chardonnay"
        )
        
        assert anomaly is None


class TestTemperatureSuboptimalDetection:
    """Tests for suboptimal temperature detection."""
    
    def test_red_wine_suboptimal_cold(self, anomaly_service: AnomalyDetectionService):
        """Red wine between critical and optimal should be warning."""
        anomaly = anomaly_service.detect_temperature_suboptimal(
            temperature_celsius=23.5,
            variety="Cabernet Sauvignon"
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.TEMPERATURE_SUBOPTIMAL.value
        assert anomaly.severity == SeverityLevel.WARNING.value
    
    def test_red_wine_suboptimal_hot(self, anomaly_service: AnomalyDetectionService):
        """Red wine above optimal range should be warning."""
        anomaly = anomaly_service.detect_temperature_suboptimal(
            temperature_celsius=31.0,
            variety="Cabernet Sauvignon"
        )
        
        assert anomaly is not None
        assert anomaly.severity == SeverityLevel.WARNING.value
    
    def test_red_wine_optimal(self, anomaly_service: AnomalyDetectionService):
        """Red wine in 24-30°C should not be flagged."""
        anomaly = anomaly_service.detect_temperature_suboptimal(
            temperature_celsius=27.0,
            variety="Cabernet Sauvignon"
        )
        
        assert anomaly is None


class TestDensityDropTooFastDetection:
    """Tests for excessive fermentation vigor detection."""
    
    def test_normal_drop(self, anomaly_service: AnomalyDetectionService):
        """Normal density drop should not trigger alert."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(hours=24), 1010.0),
            (now, 1005.0),  # 0.5% drop
        ]
        
        anomaly = anomaly_service.detect_density_drop_too_fast(previous_densities)
        assert anomaly is None
    
    def test_excessive_drop(self, anomaly_service: AnomalyDetectionService):
        """Density drop >15% in 24h should trigger alert."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(hours=24), 1000.0),
            (now, 840.0),  # 16% drop
        ]
        
        anomaly = anomaly_service.detect_density_drop_too_fast(previous_densities)
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.DENSITY_DROP_TOO_FAST.value
        assert anomaly.severity == SeverityLevel.WARNING.value


class TestHydrogenSulfideRiskDetection:
    """Tests for H2S risk detection."""
    
    def test_h2s_risk_cold_early(self, anomaly_service: AnomalyDetectionService):
        """Cold temperature in first 10 days = H2S risk."""
        anomaly = anomaly_service.detect_hydrogen_sulfide_risk(
            temperature_celsius=15.0,
            days_fermenting=5.0
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.HYDROGEN_SULFIDE_RISK.value
        assert anomaly.severity == SeverityLevel.WARNING.value
    
    def test_h2s_no_risk_warm(self, anomaly_service: AnomalyDetectionService):
        """Warm fermentation should not trigger H2S risk."""
        anomaly = anomaly_service.detect_hydrogen_sulfide_risk(
            temperature_celsius=25.0,
            days_fermenting=5.0
        )
        
        assert anomaly is None
    
    def test_h2s_no_risk_late(self, anomaly_service: AnomalyDetectionService):
        """Cold fermentation late (>10 days) is not critical for H2S."""
        anomaly = anomaly_service.detect_hydrogen_sulfide_risk(
            temperature_celsius=15.0,
            days_fermenting=15.0
        )
        
        assert anomaly is None


class TestUnusualDurationDetection:
    """Tests for unusual fermentation duration detection."""
    
    def test_typical_duration(self, anomaly_service: AnomalyDetectionService):
        """Duration within tolerance should not trigger alert."""
        anomaly = anomaly_service.detect_unusual_duration(
            days_fermenting=14.0,
            historical_avg_duration=14.0
        )
        
        assert anomaly is None
    
    def test_short_duration(self, anomaly_service: AnomalyDetectionService):
        """Duration much shorter than historical should trigger."""
        anomaly = anomaly_service.detect_unusual_duration(
            days_fermenting=10.0,
            historical_avg_duration=15.0
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.UNUSUAL_DURATION.value
        assert anomaly.severity == SeverityLevel.INFO.value
    
    def test_long_duration(self, anomaly_service: AnomalyDetectionService):
        """Duration much longer than historical should trigger."""
        anomaly = anomaly_service.detect_unusual_duration(
            days_fermenting=20.0,
            historical_avg_duration=14.0
        )
        
        assert anomaly is not None
        assert anomaly.severity == SeverityLevel.INFO.value


class TestAtypicalPatternDetection:
    """Tests for statistical outlier detection."""
    
    def test_typical_density(self, anomaly_service: AnomalyDetectionService):
        """Density within ±2σ should not trigger alert."""
        anomaly = anomaly_service.detect_atypical_pattern(
            current_density=1000.0,
            historical_densities_band={"mean": 1000.0, "stdev": 5.0}
        )
        
        assert anomaly is None
    
    def test_outlier_density(self, anomaly_service: AnomalyDetectionService):
        """Density >2σ away should trigger."""
        anomaly = anomaly_service.detect_atypical_pattern(
            current_density=1012.0,
            historical_densities_band={"mean": 1000.0, "stdev": 5.0}
        )
        
        assert anomaly is not None
        assert anomaly.anomaly_type == AnomalyType.ATYPICAL_PATTERN.value
        assert anomaly.severity == SeverityLevel.INFO.value
    
    def test_z_score_exactly_2(self, anomaly_service: AnomalyDetectionService):
        """Z-score exactly 2.0 should not trigger (need >2.0)."""
        anomaly = anomaly_service.detect_atypical_pattern(
            current_density=1010.0,
            historical_densities_band={"mean": 1000.0, "stdev": 5.0}
        )
        
        assert anomaly is None


class TestMultipleAnomaliesDetection:
    """Tests for detecting multiple anomalies simultaneously."""
    
    @pytest.mark.asyncio
    async def test_no_anomalies_normal_fermentation(self, anomaly_service: AnomalyDetectionService):
        """Normal fermentation should have no anomalies."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(days=1), 1010.0),
            (now - timedelta(hours=12), 1007.0),
            (now, 1005.0),
        ]
        
        anomalies = await anomaly_service.detect_all_anomalies(
            fermentation_id=uuid4(),
            current_density=1005.0,
            temperature_celsius=25.0,
            variety="Cabernet Sauvignon",
            days_fermenting=3.0,
            previous_densities=previous_densities,
            historical_avg_duration=14.0,
        )
        
        assert len(anomalies) == 0
    
    @pytest.mark.asyncio
    async def test_multiple_anomalies(self, anomaly_service: AnomalyDetectionService):
        """Fermentation with problems should detect multiple anomalies."""
        now = datetime.now(timezone.utc)
        previous_densities = [
            (now - timedelta(hours=13), 1005.0),
            (now, 1005.0),  # Stuck
        ]
        
        anomalies = await anomaly_service.detect_all_anomalies(
            fermentation_id=uuid4(),
            current_density=1005.0,
            temperature_celsius=28.0,  # Too warm for whites, but testing
            variety="Chardonnay",
            days_fermenting=2.0,
            previous_densities=previous_densities,
            historical_avg_duration=12.0,  # Will be unusual
        )
        
        # Should have multiple anomalies
        assert len(anomalies) > 0
        anomaly_types = [a.anomaly_type for a in anomalies]
        
        # Should include stuck fermentation
        assert AnomalyType.STUCK_FERMENTATION.value in anomaly_types

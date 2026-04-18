"""
Shared fixtures for analysis_engine tests.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore


@pytest.fixture
def winery_id():
    return uuid4()


@pytest.fixture
def fermentation_id():
    return uuid4()


@pytest.fixture
def analysis_id():
    return uuid4()


@pytest.fixture
def sample_comparison_result():
    return ComparisonResult(
        similar_fermentation_count=15,
        average_duration_days=12.5,
        average_final_gravity=1.005,
        similar_fermentation_ids=["id1", "id2"],
        comparison_basis={"variety": "Pinot Noir"},
    )


@pytest.fixture
def sample_confidence_level():
    return ConfidenceLevel(
        overall_confidence=0.75,
        historical_data_confidence=0.8,
        detection_algorithm_confidence=0.8,
        recommendation_confidence=0.7,
        sample_size=15,
        anomalies_detected=2,
        recommendations_generated=3,
    )


@pytest.fixture
def sample_analysis(winery_id, fermentation_id, sample_comparison_result, sample_confidence_level):
    return Analysis(
        fermentation_id=fermentation_id,
        winery_id=winery_id,
        comparison_result=sample_comparison_result,
        confidence_level=sample_confidence_level,
    )


@pytest.fixture
def sample_deviation_score():
    return DeviationScore(
        deviation=5.0,
        threshold=1.0,
        magnitude="HIGH",
        details={"current": 5.0, "expected": 0.0},
    )


@pytest.fixture
def sample_anomaly(analysis_id, sample_deviation_score):
    return Anomaly(
        analysis_id=analysis_id,
        anomaly_type=AnomalyType.STUCK_FERMENTATION,
        severity=SeverityLevel.CRITICAL,
        sample_id=uuid4(),
        deviation_score=sample_deviation_score,
        description="Test anomaly",
    )


@pytest.fixture
def anomaly_factory(analysis_id, sample_deviation_score):
    def _make(anomaly_type=AnomalyType.STUCK_FERMENTATION, severity=SeverityLevel.CRITICAL, description="test"):
        return Anomaly(
            analysis_id=analysis_id,
            anomaly_type=anomaly_type,
            severity=severity,
            sample_id=uuid4(),
            deviation_score=sample_deviation_score,
            description=description,
        )
    return _make


@pytest.fixture
def mock_async_session():
    """AsyncMock session for services that use AsyncSession directly."""
    session = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    result_mock.scalar_one_or_none.return_value = None
    session.execute.return_value = result_mock
    return session


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

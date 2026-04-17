"""
Tests for Anomaly domain entity.
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore


class TestAnomalyInitialization:
    def test_creates_with_required_fields(self, analysis_id, sample_deviation_score):
        anomaly = Anomaly(
            analysis_id=analysis_id,
            anomaly_type=AnomalyType.STUCK_FERMENTATION,
            severity=SeverityLevel.CRITICAL,
            sample_id=uuid4(),
            deviation_score=sample_deviation_score,
            description="Test anomaly",
        )
        assert anomaly.anomaly_type == AnomalyType.STUCK_FERMENTATION.value
        assert anomaly.severity == SeverityLevel.CRITICAL.value

    def test_enum_stored_as_string_value(self, sample_anomaly):
        assert sample_anomaly.anomaly_type == "STUCK_FERMENTATION"
        assert sample_anomaly.severity == "CRITICAL"

    def test_default_is_resolved_false(self, sample_anomaly):
        assert sample_anomaly.is_resolved is False

    def test_id_is_generated(self, sample_anomaly):
        assert sample_anomaly.id is not None

    def test_deviation_score_serialized_to_dict(self, analysis_id, sample_deviation_score):
        anomaly = Anomaly(
            analysis_id=analysis_id,
            anomaly_type=AnomalyType.STUCK_FERMENTATION,
            severity=SeverityLevel.CRITICAL,
            sample_id=uuid4(),
            deviation_score=sample_deviation_score,
            description="Test",
        )
        assert isinstance(anomaly.deviation_score, dict)
        assert anomaly.deviation_score["deviation"] == 5.0


class TestAnomalyResolve:
    def test_resolve_sets_is_resolved_true(self, sample_anomaly):
        sample_anomaly.resolve()
        assert sample_anomaly.is_resolved is True

    def test_resolve_sets_resolved_at(self, sample_anomaly):
        sample_anomaly.resolve()
        assert sample_anomaly.resolved_at is not None

    def test_resolve_raises_when_already_resolved(self, sample_anomaly):
        sample_anomaly.resolve()
        with pytest.raises(ValueError, match="already resolved"):
            sample_anomaly.resolve()


class TestAnomalyPriority:
    def test_stuck_fermentation_priority_is_1(self, sample_anomaly):
        assert sample_anomaly.priority == 1

    def test_density_drop_priority_is_2(self, analysis_id, sample_deviation_score):
        anomaly = Anomaly(
            analysis_id=analysis_id,
            anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST,
            severity=SeverityLevel.WARNING,
            sample_id=uuid4(),
            deviation_score=sample_deviation_score,
            description="density drop",
        )
        assert anomaly.priority == 2

    def test_unusual_duration_priority_is_3(self, analysis_id, sample_deviation_score):
        anomaly = Anomaly(
            analysis_id=analysis_id,
            anomaly_type=AnomalyType.UNUSUAL_DURATION,
            severity=SeverityLevel.INFO,
            sample_id=uuid4(),
            deviation_score=sample_deviation_score,
            description="unusual duration",
        )
        assert anomaly.priority == 3

    def test_all_anomaly_types_have_valid_priority(self, analysis_id, sample_deviation_score):
        for anomaly_type in AnomalyType:
            anomaly = Anomaly(
                analysis_id=analysis_id,
                anomaly_type=anomaly_type,
                severity=SeverityLevel.INFO,
                sample_id=uuid4(),
                deviation_score=sample_deviation_score,
                description="test",
            )
            assert anomaly.priority in (1, 2, 3)

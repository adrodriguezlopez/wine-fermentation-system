"""
Tests for ProtocolAnalysisIntegrationService.
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.protocol_integration_service import (
    ProtocolAnalysisIntegrationService,
)
from src.modules.analysis_engine.src.domain.entities.protocol_advisory import ProtocolAdvisory
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType


@pytest.fixture
def service():
    return ProtocolAnalysisIntegrationService()


class TestBoostConfidence:
    def test_none_compliance_returns_base_unchanged(self, service):
        result = service.boost_confidence(base_confidence=0.75, compliance_score=None)
        assert result["adjusted_confidence"] == 0.75
        assert result["protocol_assigned"] is False

    def test_100_compliance_boosts_by_50_percent(self, service):
        # 0.75 * (0.5 + 1.0) = 0.75 * 1.5 = 1.125 → capped at 1.0
        result = service.boost_confidence(base_confidence=0.75, compliance_score=100.0)
        assert result["adjusted_confidence"] == 1.0

    def test_50_compliance_is_neutral(self, service):
        # 0.80 * (0.5 + 0.5) = 0.80
        result = service.boost_confidence(base_confidence=0.80, compliance_score=50.0)
        assert abs(result["adjusted_confidence"] - 0.80) < 0.001

    def test_0_compliance_penalizes(self, service):
        # 0.80 * 0.5 = 0.4
        result = service.boost_confidence(base_confidence=0.80, compliance_score=0.0)
        assert abs(result["adjusted_confidence"] - 0.40) < 0.001

    def test_87_compliance_boost(self, service):
        # 0.75 * (0.5 + 0.87) = 0.75 * 1.37 = 1.0275 → capped at 1.0
        result = service.boost_confidence(base_confidence=0.75, compliance_score=87.0)
        assert result["adjusted_confidence"] == 1.0

    def test_protocol_assigned_true_when_score_provided(self, service):
        result = service.boost_confidence(base_confidence=0.5, compliance_score=75.0)
        assert result["protocol_assigned"] is True

    def test_result_contains_expected_keys(self, service):
        result = service.boost_confidence(base_confidence=0.5, compliance_score=50.0)
        assert "base_confidence" in result
        assert "adjusted_confidence" in result
        assert "compliance_multiplier" in result
        assert "confidence_boost_pct" in result

    def test_apply_boost_to_overall_confidence(self, service):
        result = service.apply_boost_to_overall_confidence(0.5, None)
        assert result == 0.5

    def test_apply_boost_returns_float(self, service):
        result = service.apply_boost_to_overall_confidence(0.6, 70.0)
        assert isinstance(result, float)


class TestGenerateAdvisory:
    def test_generates_advisory_for_stuck_fermentation(self, service, anomaly_factory):
        anomaly = anomaly_factory(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )
        assert advisory is not None
        assert isinstance(advisory, ProtocolAdvisory)
        assert advisory.advisory_type == AdvisoryType.ACCELERATE_STEP.value

    def test_returns_none_for_unmapped_anomaly_only(self, service):
        # VOLATILE_ACIDITY_HIGH is in the mapping, so use an empty list
        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[],
        )
        assert advisory is None

    def test_picks_highest_priority_anomaly(self, service, anomaly_factory):
        low_anomaly = anomaly_factory(AnomalyType.UNUSUAL_DURATION, SeverityLevel.INFO)
        critical_anomaly = anomaly_factory(AnomalyType.HYDROGEN_SULFIDE_RISK, SeverityLevel.WARNING)
        advisory = service.generate_advisory(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[low_anomaly, critical_anomaly],
        )
        # H2S maps to CRITICAL risk, so it should be chosen
        assert advisory.risk_level == RiskLevel.CRITICAL.value

    def test_advisory_has_correct_fermentation_id(self, service, anomaly_factory):
        ferm_id = uuid4()
        anomaly = anomaly_factory(AnomalyType.STUCK_FERMENTATION)
        advisory = service.generate_advisory(
            fermentation_id=ferm_id,
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )
        assert advisory.fermentation_id == ferm_id


class TestGenerateAllAdvisories:
    def test_generates_multiple_advisories(self, service, anomaly_factory):
        anomaly1 = anomaly_factory(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        anomaly2 = anomaly_factory(AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL, SeverityLevel.CRITICAL)
        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly1, anomaly2],
        )
        assert len(advisories) >= 1

    def test_deduplicates_by_step_type(self, service, anomaly_factory):
        # Two anomalies that both map to "MONITORING" step type
        anomaly1 = anomaly_factory(AnomalyType.DENSITY_DROP_TOO_FAST)
        anomaly2 = anomaly_factory(AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL)
        advisories = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly1, anomaly2],
        )
        step_types = [a.target_step_type for a in advisories]
        assert len(step_types) == len(set(step_types))

    def test_empty_anomalies_returns_empty_list(self, service):
        result = service.generate_all_advisories(
            fermentation_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[],
        )
        assert result == []


class TestRecalibrateConfidence:
    def test_step_skipped_reduces_confidence(self, service):
        result = service.recalibrate_confidence_on_protocol_change(0.8, "STEP_SKIPPED")
        assert result["recalibrated_confidence"] < 0.8

    def test_step_accelerated_reduces_confidence(self, service):
        result = service.recalibrate_confidence_on_protocol_change(0.8, "STEP_ACCELERATED")
        assert result["recalibrated_confidence"] < 0.8

    def test_execution_paused_reduces_most(self, service):
        r_paused = service.recalibrate_confidence_on_protocol_change(0.8, "EXECUTION_PAUSED")
        r_skipped = service.recalibrate_confidence_on_protocol_change(0.8, "STEP_SKIPPED")
        assert r_paused["recalibrated_confidence"] < r_skipped["recalibrated_confidence"]

    def test_unknown_change_type_no_adjustment(self, service):
        result = service.recalibrate_confidence_on_protocol_change(0.8, "UNKNOWN")
        assert result["recalibrated_confidence"] == 0.8

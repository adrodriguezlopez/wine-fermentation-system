"""
Tests for analysis_engine domain enums.
"""
import pytest

from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.enums.risk_level import RiskLevel
from src.modules.analysis_engine.src.domain.enums.advisory_type import AdvisoryType
from src.modules.analysis_engine.src.domain.enums.recommendation_category import RecommendationCategory


class TestAnalysisStatus:
    def test_all_values_exist(self):
        assert AnalysisStatus.PENDING.value == "PENDING"
        assert AnalysisStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert AnalysisStatus.COMPLETED.value == "COMPLETED"
        assert AnalysisStatus.FAILED.value == "FAILED"

    def test_is_final_for_completed(self):
        assert AnalysisStatus.COMPLETED.is_final is True

    def test_is_final_for_failed(self):
        assert AnalysisStatus.FAILED.is_final is True

    def test_is_not_final_for_pending(self):
        assert AnalysisStatus.PENDING.is_final is False

    def test_is_not_final_for_in_progress(self):
        assert AnalysisStatus.IN_PROGRESS.is_final is False


class TestAnomalyType:
    def test_all_8_types_exist(self):
        expected = {
            "STUCK_FERMENTATION",
            "TEMPERATURE_OUT_OF_RANGE_CRITICAL",
            "VOLATILE_ACIDITY_HIGH",
            "DENSITY_DROP_TOO_FAST",
            "HYDROGEN_SULFIDE_RISK",
            "TEMPERATURE_SUBOPTIMAL",
            "UNUSUAL_DURATION",
            "ATYPICAL_PATTERN",
        }
        actual = {at.value for at in AnomalyType}
        assert actual == expected

    def test_critical_types_have_priority_1(self):
        assert AnomalyType.STUCK_FERMENTATION.priority == 1
        assert AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL.priority == 1
        assert AnomalyType.VOLATILE_ACIDITY_HIGH.priority == 1

    def test_warning_types_have_priority_2(self):
        assert AnomalyType.DENSITY_DROP_TOO_FAST.priority == 2
        assert AnomalyType.HYDROGEN_SULFIDE_RISK.priority == 2
        assert AnomalyType.TEMPERATURE_SUBOPTIMAL.priority == 2

    def test_info_types_have_priority_3(self):
        assert AnomalyType.UNUSUAL_DURATION.priority == 3
        assert AnomalyType.ATYPICAL_PATTERN.priority == 3


class TestSeverityLevel:
    def test_all_values_exist(self):
        assert SeverityLevel.CRITICAL.value == "CRITICAL"
        assert SeverityLevel.WARNING.value == "WARNING"
        assert SeverityLevel.INFO.value == "INFO"

    def test_critical_has_highest_priority_score(self):
        assert SeverityLevel.CRITICAL.priority_score > SeverityLevel.WARNING.priority_score
        assert SeverityLevel.WARNING.priority_score > SeverityLevel.INFO.priority_score


class TestRiskLevel:
    def test_all_values_exist(self):
        assert RiskLevel.CRITICAL.value == "CRITICAL"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.LOW.value == "LOW"

    def test_priority_order(self):
        assert RiskLevel.CRITICAL.priority_score > RiskLevel.HIGH.priority_score
        assert RiskLevel.HIGH.priority_score > RiskLevel.MEDIUM.priority_score
        assert RiskLevel.MEDIUM.priority_score > RiskLevel.LOW.priority_score


class TestAdvisoryType:
    def test_all_values_exist(self):
        assert AdvisoryType.ACCELERATE_STEP.value == "ACCELERATE_STEP"
        assert AdvisoryType.SKIP_STEP.value == "SKIP_STEP"
        assert AdvisoryType.ADD_STEP.value == "ADD_STEP"

    def test_label_es_not_empty(self):
        for at in AdvisoryType:
            assert len(at.label_es) > 0

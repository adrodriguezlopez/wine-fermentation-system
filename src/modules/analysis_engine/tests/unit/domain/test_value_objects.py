"""
Tests for domain value objects: ComparisonResult, ConfidenceLevel, DeviationScore.
"""
import pytest

from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import (
    ConfidenceLevel,
    ConfidenceLevelEnum,
)
from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore


class TestComparisonResult:
    def test_creates_with_valid_data(self):
        cr = ComparisonResult(
            similar_fermentation_count=10,
            average_duration_days=14.0,
            average_final_gravity=1.002,
        )
        assert cr.similar_fermentation_count == 10

    def test_negative_count_raises(self):
        with pytest.raises(ValueError):
            ComparisonResult(similar_fermentation_count=-1, average_duration_days=None, average_final_gravity=None)

    def test_has_sufficient_data_true_when_count_gte_10(self):
        cr = ComparisonResult(similar_fermentation_count=10, average_duration_days=None, average_final_gravity=None)
        assert cr.has_sufficient_data is True

    def test_has_sufficient_data_false_when_count_lt_10(self):
        cr = ComparisonResult(similar_fermentation_count=9, average_duration_days=None, average_final_gravity=None)
        assert cr.has_sufficient_data is False

    def test_to_dict_contains_all_fields(self, sample_comparison_result):
        d = sample_comparison_result.to_dict()
        assert "similar_fermentation_count" in d
        assert "average_duration_days" in d
        assert "average_final_gravity" in d
        assert "similar_fermentation_ids" in d
        assert "comparison_basis" in d

    def test_from_dict_round_trip(self, sample_comparison_result):
        d = sample_comparison_result.to_dict()
        restored = ComparisonResult.from_dict(d)
        assert restored.similar_fermentation_count == sample_comparison_result.similar_fermentation_count
        assert restored.average_duration_days == sample_comparison_result.average_duration_days

    def test_historical_samples_count_alias(self, sample_comparison_result):
        assert sample_comparison_result.historical_samples_count == sample_comparison_result.similar_fermentation_count

    def test_from_dict_defaults_on_missing_keys(self):
        cr = ComparisonResult.from_dict({})
        assert cr.similar_fermentation_count == 0
        assert cr.average_duration_days is None


class TestConfidenceLevel:
    def test_creates_with_valid_data(self, sample_confidence_level):
        assert sample_confidence_level.overall_confidence == 0.75
        assert sample_confidence_level.sample_size == 15

    def test_confidence_out_of_range_raises(self):
        with pytest.raises(ValueError):
            ConfidenceLevel(
                overall_confidence=1.5,
                historical_data_confidence=0.8,
                detection_algorithm_confidence=0.8,
                recommendation_confidence=0.7,
                sample_size=10,
                anomalies_detected=0,
                recommendations_generated=0,
            )

    def test_negative_sample_size_raises(self):
        with pytest.raises(ValueError):
            ConfidenceLevel(
                overall_confidence=0.5,
                historical_data_confidence=0.5,
                detection_algorithm_confidence=0.5,
                recommendation_confidence=0.5,
                sample_size=-1,
                anomalies_detected=0,
                recommendations_generated=0,
            )

    def test_level_very_high_when_confidence_gte_75(self, sample_confidence_level):
        assert sample_confidence_level.level == ConfidenceLevelEnum.VERY_HIGH

    def test_level_low_when_confidence_below_35(self):
        cl = ConfidenceLevel(
            overall_confidence=0.2,
            historical_data_confidence=0.2,
            detection_algorithm_confidence=0.2,
            recommendation_confidence=0.2,
            sample_size=2,
            anomalies_detected=0,
            recommendations_generated=0,
        )
        assert cl.level == ConfidenceLevelEnum.LOW

    def test_to_dict_round_trip(self, sample_confidence_level):
        d = sample_confidence_level.to_dict()
        restored = ConfidenceLevel.from_dict(d)
        assert restored.overall_confidence == sample_confidence_level.overall_confidence
        assert restored.sample_size == sample_confidence_level.sample_size

    def test_should_apply_statistical_analysis_true_when_sample_gte_10(self, sample_confidence_level):
        assert sample_confidence_level.should_apply_statistical_analysis is True

    def test_should_apply_statistical_analysis_false_when_sample_lt_10(self):
        cl = ConfidenceLevel(
            overall_confidence=0.5,
            historical_data_confidence=0.5,
            detection_algorithm_confidence=0.5,
            recommendation_confidence=0.5,
            sample_size=5,
            anomalies_detected=0,
            recommendations_generated=0,
        )
        assert cl.should_apply_statistical_analysis is False

    def test_calculate_level_from_count_low(self):
        assert ConfidenceLevel.calculate_level_from_count(3) == ConfidenceLevelEnum.LOW

    def test_calculate_level_from_count_medium(self):
        assert ConfidenceLevel.calculate_level_from_count(10) == ConfidenceLevelEnum.MEDIUM

    def test_calculate_level_from_count_high(self):
        assert ConfidenceLevel.calculate_level_from_count(20) == ConfidenceLevelEnum.HIGH

    def test_calculate_level_from_count_very_high(self):
        assert ConfidenceLevel.calculate_level_from_count(35) == ConfidenceLevelEnum.VERY_HIGH


class TestDeviationScore:
    def test_creates_in_simplified_mode(self, sample_deviation_score):
        assert sample_deviation_score.deviation == 5.0
        assert sample_deviation_score.threshold == 1.0
        assert sample_deviation_score.magnitude == "HIGH"

    def test_creates_in_statistical_mode(self):
        ds = DeviationScore(
            deviation=3.5,
            metric_name="density",
            current_value=5.5,
            expected_value=2.0,
            z_score=2.5,
            percentile=99.0,
            is_significant=True,
        )
        assert ds.z_score == 2.5
        assert ds.is_significant is True

    def test_extreme_z_score_raises(self):
        with pytest.raises(ValueError):
            DeviationScore(deviation=1.0, z_score=11.0)

    def test_percentile_out_of_range_raises(self):
        with pytest.raises(ValueError):
            DeviationScore(deviation=1.0, percentile=101.0)

    def test_severity_indicator_high_magnitude(self, sample_deviation_score):
        assert sample_deviation_score.severity_indicator == "critical"

    def test_severity_indicator_from_z_score(self):
        ds = DeviationScore(deviation=1.0, z_score=3.5)
        assert ds.severity_indicator == "critical"

    def test_to_dict_contains_deviation(self, sample_deviation_score):
        d = sample_deviation_score.to_dict()
        assert "deviation" in d
        assert d["deviation"] == 5.0

    def test_from_dict_round_trip(self, sample_deviation_score):
        d = sample_deviation_score.to_dict()
        restored = DeviationScore.from_dict(d)
        assert restored.deviation == sample_deviation_score.deviation
        assert restored.threshold == sample_deviation_score.threshold

    def test_is_extreme_true_when_percentile_below_5(self):
        ds = DeviationScore(deviation=1.0, percentile=2.0)
        assert ds.is_extreme is True

    def test_is_extreme_false_when_percentile_normal(self):
        ds = DeviationScore(deviation=1.0, percentile=50.0)
        assert ds.is_extreme is False

"""
Tests for Analysis domain entity.
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel


class TestAnalysisInitialization:
    def test_creates_with_required_fields(self, winery_id, fermentation_id):
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={},
            confidence_level={},
        )
        assert analysis.fermentation_id == fermentation_id
        assert analysis.winery_id == winery_id

    def test_default_status_is_pending(self, sample_analysis):
        assert sample_analysis.status == AnalysisStatus.PENDING.value

    def test_id_is_generated(self, sample_analysis):
        assert sample_analysis.id is not None

    def test_comparison_result_serialized_from_value_object(self, winery_id, fermentation_id, sample_comparison_result):
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result=sample_comparison_result,
            confidence_level={},
        )
        assert isinstance(analysis.comparison_result, dict)
        assert analysis.comparison_result["similar_fermentation_count"] == 15

    def test_confidence_level_serialized_from_value_object(self, winery_id, fermentation_id, sample_confidence_level):
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result={},
            confidence_level=sample_confidence_level,
        )
        assert isinstance(analysis.confidence_level, dict)
        assert analysis.confidence_level["overall_confidence"] == 0.75


class TestAnalysisLifecycle:
    def test_start_transitions_to_in_progress(self, sample_analysis):
        sample_analysis.start()
        assert sample_analysis.status == AnalysisStatus.IN_PROGRESS.value

    def test_start_raises_when_not_pending(self, sample_analysis):
        sample_analysis.start()
        with pytest.raises(ValueError, match="PENDING"):
            sample_analysis.start()

    def test_complete_transitions_to_completed(self, sample_analysis):
        sample_analysis.start()
        sample_analysis.complete()
        assert sample_analysis.status == AnalysisStatus.COMPLETED.value

    def test_complete_raises_when_not_in_progress(self, sample_analysis):
        with pytest.raises(ValueError, match="IN_PROGRESS"):
            sample_analysis.complete()

    def test_fail_sets_status_to_failed(self, sample_analysis):
        sample_analysis.fail("something went wrong")
        assert sample_analysis.status == AnalysisStatus.FAILED.value

    def test_fail_works_from_any_status(self, sample_analysis):
        sample_analysis.start()
        sample_analysis.fail("error mid-run")
        assert sample_analysis.status == AnalysisStatus.FAILED.value


class TestAnalysisProperties:
    def test_is_completed_false_while_pending(self, sample_analysis):
        assert not sample_analysis.is_completed

    def test_is_completed_true_when_completed(self, sample_analysis):
        sample_analysis.start()
        sample_analysis.complete()
        assert sample_analysis.is_completed

    def test_is_completed_true_when_failed(self, sample_analysis):
        sample_analysis.fail("err")
        assert sample_analysis.is_completed

    def test_has_anomalies_false_initially(self, sample_analysis):
        assert not sample_analysis.has_anomalies

    def test_critical_anomalies_count_zero_initially(self, sample_analysis):
        assert sample_analysis.critical_anomalies_count == 0

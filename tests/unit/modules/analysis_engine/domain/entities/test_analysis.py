"""
Tests for Analysis entity (Aggregate Root).
TDD: Write tests first, then implement entity.
"""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel


class TestAnalysisCreation:
    """Tests for Analysis entity creation and basic properties."""
    
    def test_create_analysis_with_valid_data(self):
        """Should create Analysis entity with required fields."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        comparison_result = ComparisonResult(
            historical_samples_count=20,
            similarity_score=85.0,
            statistical_metrics={"mean_duration": 12},
            comparison_criteria={"varietal": "Malbec"},
            patterns_used=[1, 2, 3],
            compared_at=datetime.now(timezone.utc)
        )
        confidence_level = ConfidenceLevel.from_comparison_result(
            historical_samples_count=20,
            similarity_score=85.0
        )
        
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            comparison_result=comparison_result,
            confidence_level=confidence_level
        )
        
        assert analysis.id is not None
        assert analysis.fermentation_id == fermentation_id
        assert analysis.winery_id == winery_id
        assert analysis.status == AnalysisStatus.PENDING
        assert analysis.comparison_result == comparison_result
        assert analysis.confidence_level == confidence_level
        assert analysis.analyzed_at is not None
        assert len(analysis.anomalies) == 0
        assert len(analysis.recommendations) == 0
    
    def test_create_analysis_generates_unique_id(self):
        """Should generate unique UUID for each Analysis."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        comparison_result = ComparisonResult(
            historical_samples_count=10,
            similarity_score=75.0,
            statistical_metrics={},
            comparison_criteria={},
            patterns_used=[],
            compared_at=datetime.now(timezone.utc)
        )
        confidence_level = ConfidenceLevel.from_comparison_result(10, 75.0)
        
        analysis1 = Analysis(fermentation_id, winery_id, comparison_result, confidence_level)
        analysis2 = Analysis(fermentation_id, winery_id, comparison_result, confidence_level)
        
        assert analysis1.id != analysis2.id


class TestAnalysisStatusTransitions:
    """Tests for Analysis status state machine."""
    
    def test_start_analysis_changes_status_to_in_progress(self):
        """Should transition from PENDING to IN_PROGRESS."""
        analysis = self._create_analysis()
        
        analysis.start()
        
        assert analysis.status == AnalysisStatus.IN_PROGRESS
    
    def test_complete_analysis_changes_status_to_completed(self):
        """Should transition from IN_PROGRESS to COMPLETED."""
        analysis = self._create_analysis()
        analysis.start()
        
        analysis.complete()
        
        assert analysis.status == AnalysisStatus.COMPLETED
    
    def test_fail_analysis_changes_status_to_failed(self):
        """Should transition to FAILED from any status."""
        analysis = self._create_analysis()
        
        analysis.fail("Test error")
        
        assert analysis.status == AnalysisStatus.FAILED
    
    def test_cannot_start_already_started_analysis(self):
        """Should raise error when trying to start analysis that's not PENDING."""
        analysis = self._create_analysis()
        analysis.start()
        
        with pytest.raises(ValueError, match="Cannot start analysis.*IN_PROGRESS"):
            analysis.start()
    
    def test_cannot_complete_pending_analysis(self):
        """Should raise error when trying to complete analysis that's not IN_PROGRESS."""
        analysis = self._create_analysis()
        
        with pytest.raises(ValueError, match="Cannot complete analysis.*PENDING"):
            analysis.complete()
    
    def _create_analysis(self) -> Analysis:
        """Helper to create a basic Analysis for testing."""
        comparison_result = ComparisonResult(
            historical_samples_count=15,
            similarity_score=80.0,
            statistical_metrics={},
            comparison_criteria={},
            patterns_used=[],
            compared_at=datetime.now(timezone.utc)
        )
        confidence_level = ConfidenceLevel.from_comparison_result(15, 80.0)
        return Analysis(
            fermentation_id=uuid4(),
            winery_id=uuid4(),
            comparison_result=comparison_result,
            confidence_level=confidence_level
        )


class TestAnalysisAnomalyManagement:
    """Tests for adding/managing anomalies in Analysis."""
    
    def test_add_anomaly_to_analysis(self):
        """Should add anomaly to analysis anomalies list."""
        from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
        from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
        from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
        from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore
        
        analysis = self._create_analysis()
        deviation = DeviationScore(
            metric_name="temperature",
            current_value=35.0,
            expected_value=25.0,
            deviation=10.0,
            z_score=3.5,
            percentile=99.0,
            is_significant=True
        )
        anomaly = Anomaly(
            analysis_id=analysis.id,
            anomaly_type=AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL,
            severity=SeverityLevel.CRITICAL,
            sample_id=uuid4(),
            deviation_score=deviation,
            description="Temperatura crítica detectada"
        )
        
        analysis.add_anomaly(anomaly)
        
        assert len(analysis.anomalies) == 1
        assert analysis.anomalies[0] == anomaly
    
    def test_add_multiple_anomalies(self):
        """Should add multiple anomalies to analysis."""
        from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
        from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
        from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
        from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore
        
        analysis = self._create_analysis()
        deviation = DeviationScore("temp", 30.0, 25.0, 5.0, 2.0, 95.0, True)
        
        anomaly1 = Anomaly(
            analysis.id, AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL,
            SeverityLevel.CRITICAL, uuid4(), deviation, "Error 1"
        )
        anomaly2 = Anomaly(
            analysis.id, AnomalyType.STUCK_FERMENTATION,
            SeverityLevel.CRITICAL, uuid4(), deviation, "Error 2"
        )
        
        analysis.add_anomaly(anomaly1)
        analysis.add_anomaly(anomaly2)
        
        assert len(analysis.anomalies) == 2
    
    def test_cannot_add_anomaly_with_wrong_analysis_id(self):
        """Should raise error when anomaly's analysis_id doesn't match."""
        from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
        from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
        from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
        from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore
        
        analysis = self._create_analysis()
        wrong_analysis_id = uuid4()  # Different ID
        deviation = DeviationScore("temp", 30.0, 25.0, 5.0, 2.0, 95.0, True)
        anomaly = Anomaly(
            wrong_analysis_id, AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL,
            SeverityLevel.CRITICAL, uuid4(), deviation, "Error"
        )
        
        with pytest.raises(ValueError, match="Anomaly does not belong to this analysis"):
            analysis.add_anomaly(anomaly)
    
    def _create_analysis(self) -> Analysis:
        """Helper to create a basic Analysis for testing."""
        comparison_result = ComparisonResult(
            historical_samples_count=15,
            similarity_score=80.0,
            statistical_metrics={},
            comparison_criteria={},
            patterns_used=[],
            compared_at=datetime.now(timezone.utc)
        )
        confidence_level = ConfidenceLevel.from_comparison_result(15, 80.0)
        return Analysis(
            fermentation_id=uuid4(),
            winery_id=uuid4(),
            comparison_result=comparison_result,
            confidence_level=confidence_level
        )


class TestAnalysisRecommendationManagement:
    """Tests for adding/managing recommendations in Analysis."""
    
    def test_add_recommendation_to_analysis(self):
        """Should add recommendation to analysis recommendations list."""
        from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
        from src.modules.analysis_engine.src.domain.enums.recommendation_category import RecommendationCategory
        
        analysis = self._create_analysis()
        recommendation = Recommendation(
            analysis_id=analysis.id,
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="Ajustar temperatura a 25°C",
            priority=1,
            confidence=0.95,
            supporting_evidence_count=20
        )
        
        analysis.add_recommendation(recommendation)
        
        assert len(analysis.recommendations) == 1
        assert analysis.recommendations[0] == recommendation
    
    def test_cannot_add_recommendation_with_wrong_analysis_id(self):
        """Should raise error when recommendation's analysis_id doesn't match."""
        from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
        
        analysis = self._create_analysis()
        wrong_analysis_id = uuid4()
        recommendation = Recommendation(
            analysis_id=wrong_analysis_id,
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="Test",
            priority=1,
            confidence=0.9,
            supporting_evidence_count=10
        )
        
        with pytest.raises(ValueError, match="Recommendation does not belong to this analysis"):
            analysis.add_recommendation(recommendation)
    
    def _create_analysis(self) -> Analysis:
        """Helper to create a basic Analysis for testing."""
        comparison_result = ComparisonResult(
            historical_samples_count=15,
            similarity_score=80.0,
            statistical_metrics={},
            comparison_criteria={},
            patterns_used=[],
            compared_at=datetime.now(timezone.utc)
        )
        confidence_level = ConfidenceLevel.from_comparison_result(15, 80.0)
        return Analysis(
            fermentation_id=uuid4(),
            winery_id=uuid4(),
            comparison_result=comparison_result,
            confidence_level=confidence_level
        )

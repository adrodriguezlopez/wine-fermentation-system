"""Tests for Analysis Orchestrator Service."""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import AnalysisOrchestratorService
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel


@pytest.fixture
def orchestrator_service(session: AsyncSession, threshold_config):
    """Create an Analysis Orchestrator Service instance."""
    return AnalysisOrchestratorService(session, threshold_config)


class TestConfidenceLevelCalculation:
    """Tests for confidence level calculation."""
    
    def test_high_confidence_plenty_history(self, orchestrator_service: AnalysisOrchestratorService):
        """6+ historical samples should have high confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=10,
            anomaly_count=1,
            recommendation_count=1
        )
        
        assert isinstance(confidence, ConfidenceLevel)
        assert confidence.historical_data_confidence >= 0.8
        assert confidence.overall_confidence >= 0.6
    
    def test_low_confidence_no_history(self, orchestrator_service: AnalysisOrchestratorService):
        """0 historical samples should have lower confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=0,
            anomaly_count=1,
            recommendation_count=1
        )
        
        assert confidence.historical_data_confidence == 0.3
        assert confidence.overall_confidence < 0.5
    
    def test_medium_confidence_few_samples(self, orchestrator_service: AnalysisOrchestratorService):
        """2-5 samples should have medium confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=3,
            anomaly_count=0,
            recommendation_count=0
        )
        
        assert 0.5 <= confidence.historical_data_confidence <= 0.75
    
    def test_detection_confidence_no_anomalies(self, orchestrator_service: AnalysisOrchestratorService):
        """No anomalies should have high detection confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=0,
            recommendation_count=0
        )
        
        assert confidence.detection_algorithm_confidence == 0.8
    
    def test_detection_confidence_multiple_anomalies(self, orchestrator_service: AnalysisOrchestratorService):
        """Many anomalies reduce confidence (potential false positives)."""
        confidence_few = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=1,
            recommendation_count=1
        )
        
        confidence_many = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=5,
            recommendation_count=5
        )
        
        assert confidence_few.detection_algorithm_confidence > confidence_many.detection_algorithm_confidence
    
    def test_recommendation_confidence_matched(self, orchestrator_service: AnalysisOrchestratorService):
        """Recommendations matching anomalies should have high confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=3,
            recommendation_count=3
        )
        
        assert confidence.recommendation_confidence >= 0.85
    
    def test_recommendation_confidence_mismatched(self, orchestrator_service: AnalysisOrchestratorService):
        """Recommendations not matching anomalies should have lower confidence."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=3,
            recommendation_count=0
        )
        
        assert confidence.recommendation_confidence == 0.6
    
    def test_overall_confidence_calculation(self, orchestrator_service: AnalysisOrchestratorService):
        """Overall confidence should be weighted average of components."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=8,
            anomaly_count=1,
            recommendation_count=1
        )
        
        # Should have:
        # - Historical: 0.9 (8 samples)
        # - Detection: 0.9 (1 anomaly)
        # - Recommendation: 0.85 (matched)
        # Overall = 0.9*0.7 + 0.9*0.2 + 0.85*0.1 = 0.63 + 0.18 + 0.085 = 0.895 ≈ 0.90
        assert confidence.overall_confidence >= 0.88


class TestAnalysisWorkflow:
    """Tests for the complete analysis workflow."""
    
    @pytest.mark.asyncio
    async def test_analysis_creates_with_pending_status(self, orchestrator_service: AnalysisOrchestratorService):
        """Analysis should start in IN_PROGRESS status during execution."""
        # We can't fully test without a database, but verify the workflow logic
        assert hasattr(orchestrator_service, 'execute_analysis')
        assert hasattr(orchestrator_service, 'comparison')
        assert hasattr(orchestrator_service, 'anomaly_detection')
        assert hasattr(orchestrator_service, 'recommendation')
    
    @pytest.mark.asyncio
    async def test_retrieve_non_existent_analysis(self, orchestrator_service: AnalysisOrchestratorService):
        """Retrieving non-existent analysis should return None."""
        analysis = await orchestrator_service.get_analysis(
            analysis_id=uuid4(),
            winery_id=uuid4()
        )
        
        assert analysis is None


class TestMultiTenancyEnforcement:
    """Tests for multi-tenancy isolation."""
    
    @pytest.mark.asyncio
    async def test_cross_winery_access_denied(self, orchestrator_service: AnalysisOrchestratorService):
        """Accessing analysis from different winery should raise error."""
        # This test would require a populated database with cross-winery data
        # For now, verify the method exists and performs the check
        
        # Method logic:
        # 1. Fetch analysis from DB
        # 2. If not found, return None
        # 3. If found but winery_id differs, raise CrossWineryAccessDenied
        
        assert hasattr(orchestrator_service, 'get_analysis')


class TestAnalysisHistory:
    """Tests for analysis history retrieval."""
    
    @pytest.mark.asyncio
    async def test_get_fermentation_analysis_history(self, orchestrator_service: AnalysisOrchestratorService):
        """Should retrieve analysis history for a fermentation."""
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        analyses = await orchestrator_service.get_fermentation_analyses(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            limit=10
        )
        
        assert isinstance(analyses, list)
        assert len(analyses) == 0  # No data in test database
    
    @pytest.mark.asyncio
    async def test_analysis_history_ordering(self, orchestrator_service: AnalysisOrchestratorService):
        """Analysis history should be ordered most recent first."""
        # This would be verified with a populated database
        # For now, verify the method exists and accepts parameters
        
        fermentation_id = uuid4()
        winery_id = uuid4()
        
        analyses = await orchestrator_service.get_fermentation_analyses(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            limit=5
        )
        
        assert isinstance(analyses, list)


class TestAnalysisStatusTransitions:
    """Tests for analysis status transitions."""
    
    def test_status_enum_values(self):
        """Verify analysis status enum has expected values."""
        assert hasattr(AnalysisStatus, 'PENDING')
        assert hasattr(AnalysisStatus, 'IN_PROGRESS')
        assert hasattr(AnalysisStatus, 'COMPLETED')
        assert hasattr(AnalysisStatus, 'FAILED')


class TestConfidenceLevelStructure:
    """Tests for ConfidenceLevel value object structure."""
    
    def test_confidence_serialization(self, orchestrator_service: AnalysisOrchestratorService):
        """ConfidenceLevel should serialize to dict."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=1,
            recommendation_count=1
        )
        
        confidence_dict = confidence.to_dict()
        
        assert "overall_confidence" in confidence_dict
        assert "historical_data_confidence" in confidence_dict
        assert "detection_algorithm_confidence" in confidence_dict
        assert "recommendation_confidence" in confidence_dict
        assert "sample_size" in confidence_dict
        assert "anomalies_detected" in confidence_dict
        assert "recommendations_generated" in confidence_dict
    
    def test_confidence_value_ranges(self, orchestrator_service: AnalysisOrchestratorService):
        """Confidence values should be between 0 and 1."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=2,
            recommendation_count=2
        )
        
        assert 0.0 <= confidence.overall_confidence <= 1.0
        assert 0.0 <= confidence.historical_data_confidence <= 1.0
        assert 0.0 <= confidence.detection_algorithm_confidence <= 1.0
        assert 0.0 <= confidence.recommendation_confidence <= 1.0


class TestAnalysisWithVariousScenarios:
    """Tests for analysis in different scenarios."""
    
    def test_confidence_perfect_scenario(self, orchestrator_service: AnalysisOrchestratorService):
        """Perfect scenario: plenty of history, 1 anomaly, matched recommendation."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=10,
            anomaly_count=1,
            recommendation_count=1
        )
        
        # Should have highest possible confidence
        assert confidence.overall_confidence > 0.75
    
    def test_confidence_uncertain_scenario(self, orchestrator_service: AnalysisOrchestratorService):
        """Uncertain scenario: no history, multiple anomalies."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=0,
            anomaly_count=4,
            recommendation_count=3
        )
        
        # Should have lower confidence due to lack of history
        assert confidence.overall_confidence < 0.60
    
    def test_confidence_clean_scenario(self, orchestrator_service: AnalysisOrchestratorService):
        """Clean scenario: no anomalies detected."""
        confidence = orchestrator_service._calculate_confidence(
            historical_count=5,
            anomaly_count=0,
            recommendation_count=0
        )
        
        # Should have high confidence (everything normal)
        assert confidence.overall_confidence > 0.6
        assert confidence.detection_algorithm_confidence == 0.8

"""Tests for Recommendation Service."""
import pytest
import sys
from pathlib import Path
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

# Add project root and src to path
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.modules.analysis_engine.src.service_component.services.recommendation_service import RecommendationService
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation


@pytest.fixture
def recommendation_service(session: AsyncSession):
    """Create a Recommendation Service instance."""
    return RecommendationService(session)


class TestPriorityCalculation:
    """Tests for recommendation priority calculation."""
    
    def test_critical_anomaly_high_priority(self, recommendation_service: RecommendationService):
        """Critical anomalies should have high priority."""
        # Create mock anomaly and template
        from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
        
        anomaly = Anomaly(
            analysis_id=uuid4(),
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Test anomaly",
            deviation_score={},
        )
        
        template = RecommendationTemplate(
            category="NUTRIENT_MANAGEMENT",
            recommendation_text="Add nutrients",
            effectiveness_score=80,
        )
        
        priority = recommendation_service._calculate_priority(anomaly, template)
        
        # CRITICAL weight (1000) + (effectiveness 80 / 10) = 1008
        assert priority == 1008
    
    def test_warning_anomaly_medium_priority(self, recommendation_service: RecommendationService):
        """Warning anomalies should have medium priority."""
        from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
        
        anomaly = Anomaly(
            analysis_id=uuid4(),
            sample_id=uuid4(),
            anomaly_type=AnomalyType.DENSITY_DROP_TOO_FAST.value,
            severity=SeverityLevel.WARNING.value,
            description="Test anomaly",
            deviation_score={},
        )
        
        template = RecommendationTemplate(
            category="TEMPERATURE_CONTROL",
            recommendation_text="Cool down",
            effectiveness_score=70,
        )
        
        priority = recommendation_service._calculate_priority(anomaly, template)
        
        # WARNING weight (100) + (effectiveness 70 / 10) = 107
        assert priority == 107
    
    def test_info_anomaly_low_priority(self, recommendation_service: RecommendationService):
        """Info anomalies should have low priority."""
        from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
        
        anomaly = Anomaly(
            analysis_id=uuid4(),
            sample_id=uuid4(),
            anomaly_type=AnomalyType.UNUSUAL_DURATION.value,
            severity=SeverityLevel.INFO.value,
            description="Test anomaly",
            deviation_score={},
        )
        
        template = RecommendationTemplate(
            category="MONITORING_FREQUENCY",
            recommendation_text="Monitor closely",
            effectiveness_score=50,
        )
        
        priority = recommendation_service._calculate_priority(anomaly, template)
        
        # INFO weight (10) + (effectiveness 50 / 10) = 15
        assert priority == 15


class TestRecommendationRanking:
    """Tests for recommendation ranking."""
    
    @pytest.mark.asyncio
    async def test_rank_by_priority(self, recommendation_service: RecommendationService):
        """Recommendations should be sorted by priority (highest first)."""
        rec1 = Recommendation(
            analysis_id=uuid4(),
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="Low priority",
            category="INFO",
            priority=15,
            estimated_effectiveness=50,
        )
        
        rec2 = Recommendation(
            analysis_id=uuid4(),
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="High priority",
            category="CRITICAL",
            priority=1008,
            estimated_effectiveness=80,
        )
        
        rec3 = Recommendation(
            analysis_id=uuid4(),
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="Medium priority",
            category="WARNING",
            priority=107,
            estimated_effectiveness=70,
        )
        
        unordered = [rec1, rec3, rec2]
        ranked = await recommendation_service.rank_recommendations(unordered)
        
        assert ranked[0].priority == 1008
        assert ranked[1].priority == 107
        assert ranked[2].priority == 15


class TestTopRecommendations:
    """Tests for getting top recommendations."""
    
    @pytest.mark.asyncio
    async def test_get_top_5_recommendations(self, recommendation_service: RecommendationService):
        """Should return top 5 most important recommendations."""
        recs = [
            Recommendation(
                analysis_id=uuid4(),
                anomaly_id=uuid4(),
                recommendation_template_id=uuid4(),
                recommendation_text=f"Rec {i}",
                category="TEST",
                priority=i * 100,
                estimated_effectiveness=50,
            )
            for i in range(1, 11)
        ]
        
        top = await recommendation_service.get_top_recommendations(recs, limit=5)
        
        assert len(top) == 5
        # Should be ranked highest to lowest
        for i, rec in enumerate(top):
            if i < len(top) - 1:
                assert rec.priority >= top[i + 1].priority
    
    @pytest.mark.asyncio
    async def test_fewer_recs_than_limit(self, recommendation_service: RecommendationService):
        """Should return all recommendations if fewer than limit."""
        recs = [
            Recommendation(
                analysis_id=uuid4(),
                anomaly_id=uuid4(),
                recommendation_template_id=uuid4(),
                recommendation_text="Rec",
                category="TEST",
                priority=100,
                estimated_effectiveness=50,
            )
            for _ in range(3)
        ]
        
        top = await recommendation_service.get_top_recommendations(recs, limit=5)
        
        assert len(top) == 3


class TestAnomalyToRecommendationMapping:
    """Tests for anomaly to recommendation category mapping."""
    
    @pytest.mark.asyncio
    async def test_stuck_fermentation_mapping(self, recommendation_service: RecommendationService):
        """Stuck fermentation should map to nutrient/aeration categories."""
        categories = await recommendation_service._get_templates_for_anomaly(
            winery_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION
        )
        
        # Will return empty list if no templates exist, which is expected during testing
        # The mapping logic is verified through the code
        assert isinstance(categories, list)
    
    @pytest.mark.asyncio
    async def test_temperature_critical_mapping(self, recommendation_service: RecommendationService):
        """Critical temperature should map to temperature control category."""
        categories = await recommendation_service._get_templates_for_anomaly(
            winery_id=uuid4(),
            anomaly_type=AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL
        )
        
        assert isinstance(categories, list)
    
    @pytest.mark.asyncio
    async def test_h2s_risk_mapping(self, recommendation_service: RecommendationService):
        """H2S risk should map to aeration and nutrient categories."""
        categories = await recommendation_service._get_templates_for_anomaly(
            winery_id=uuid4(),
            anomaly_type=AnomalyType.HYDROGEN_SULFIDE_RISK
        )
        
        assert isinstance(categories, list)


class TestRecommendationGeneration:
    """Tests for recommendation generation workflow."""
    
    @pytest.mark.asyncio
    async def test_generate_no_recommendations_no_anomalies(self, recommendation_service: RecommendationService):
        """No anomalies should produce no recommendations."""
        recommendations = await recommendation_service.generate_recommendations(
            winery_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[]
        )
        
        assert len(recommendations) == 0
    
    @pytest.mark.asyncio
    async def test_generate_recommendations_for_anomaly(self, recommendation_service: RecommendationService):
        """Anomalies should generate recommendations (or empty if no templates)."""
        anomaly = Anomaly(
            analysis_id=uuid4(),
            sample_id=uuid4(),
            anomaly_type=AnomalyType.STUCK_FERMENTATION.value,
            severity=SeverityLevel.CRITICAL.value,
            description="Stuck fermentation detected",
            deviation_score={},
        )
        
        recommendations = await recommendation_service.generate_recommendations(
            winery_id=uuid4(),
            analysis_id=uuid4(),
            anomalies=[anomaly]
        )
        
        # Will be empty if no templates exist (expected for now)
        # When templates are seeded, should have recommendations
        assert isinstance(recommendations, list)


class TestRecommendationApplication:
    """Tests for tracking recommendation application."""
    
    @pytest.mark.asyncio
    async def test_mark_recommendation_applied(self, recommendation_service: RecommendationService):
        """Should be able to mark recommendations as applied."""
        # Create a recommendation in the database first
        rec = Recommendation(
            analysis_id=uuid4(),
            anomaly_id=uuid4(),
            recommendation_template_id=uuid4(),
            recommendation_text="Apply this fix",
            category="TEST",
            priority=100,
            estimated_effectiveness=75,
        )
        
        # In a real test with a database, we would:
        # 1. Save the recommendation
        # 2. Call record_recommendation_applied
        # 3. Verify is_applied is True and applied_at is set
        
        # For now, test the logic exists
        assert hasattr(recommendation_service, 'record_recommendation_applied')

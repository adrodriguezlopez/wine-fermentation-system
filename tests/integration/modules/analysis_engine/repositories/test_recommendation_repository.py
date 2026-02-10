"""
Integration tests for RecommendationRepository.

Tests cover all methods of IRecommendationRepository interface with real database operations.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.entities.anomaly import Anomaly
from src.modules.analysis_engine.src.domain.entities.recommendation import Recommendation
from src.modules.analysis_engine.src.domain.entities.recommendation_template import RecommendationTemplate
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
from src.modules.analysis_engine.src.domain.enums.recommendation_category import RecommendationCategory


@pytest.mark.integration
class TestRecommendationRepositoryGetById:
    """Test recommendation retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_existing_recommendation(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test getting an existing recommendation."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control fermentation temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        recommendation = Recommendation(
            analysis_id=analysis.id,
            recommendation_template_id=template.id,
            recommendation_text="Increase fermentation temperature by 2°C",
            priority=1,
            confidence=0.95,
            supporting_evidence_count=3
        )
        db_session.add(recommendation)
        await db_session.flush()
        
        retrieved = await recommendation_repository.get_by_id(recommendation.id)
        
        assert retrieved is not None
        assert retrieved.id == recommendation.id
        assert retrieved.recommendation_text == "Increase fermentation temperature by 2°C"

    @pytest.mark.asyncio
    async def test_get_nonexistent_recommendation_returns_none(self, recommendation_repository):
        """Test getting a nonexistent recommendation returns None."""
        result = await recommendation_repository.get_by_id(uuid4())
        assert result is None


@pytest.mark.integration
class TestRecommendationRepositoryGetByAnalysis:
    """Test getting recommendations by analysis."""

    @pytest.mark.asyncio
    async def test_get_by_analysis_id(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test getting all recommendations for an analysis."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template1 = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        template2 = RecommendationTemplate(
            code="NUTRIENT_ADD",
            category=RecommendationCategory.NUTRIENT_ADDITION.value,
            title="Nutrient Addition",
            description="Add nutrients",
            applicable_anomaly_types=[AnomalyType.DENSITY_DROP_TOO_FAST.value],
            priority_default=2
        )
        db_session.add_all([template1, template2])
        await db_session.flush()
        
        rec1 = Recommendation(
            analysis_id=analysis.id,
            recommendation_template_id=template1.id,
            recommendation_text="Increase temperature",
            priority=1,
            confidence=0.95,
            supporting_evidence_count=3
        )
        rec2 = Recommendation(
            analysis_id=analysis.id,
            recommendation_template_id=template2.id,
            recommendation_text="Add nutrients",
            priority=2,
            confidence=0.80,
            supporting_evidence_count=2
        )
        db_session.add_all([rec1, rec2])
        await db_session.flush()
        
        recommendations = await recommendation_repository.get_by_analysis_id(analysis.id)
        
        assert len(recommendations) == 2
        assert recommendations[0].priority == 2  # Ordered by priority descending


@pytest.mark.integration
class TestRecommendationRepositoryListUnapplied:
    """Test listing unapplied recommendations."""

    @pytest.mark.asyncio
    async def test_list_unapplied(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test listing unapplied recommendations."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        unapplied = Recommendation(
            analysis_id=analysis.id,
            recommendation_template_id=template.id,
            recommendation_text="Increase temperature",
            priority=1,
            confidence=0.95,
            supporting_evidence_count=3,
            is_applied=False
        )
        applied = Recommendation(
            analysis_id=analysis.id,
            recommendation_template_id=template.id,
            recommendation_text="Decrease pH",
            priority=2,
            confidence=0.85,
            supporting_evidence_count=2,
            is_applied=True,
            applied_at=datetime.now(timezone.utc)
        )
        db_session.add_all([unapplied, applied])
        await db_session.flush()
        
        recommendations = await recommendation_repository.list_unapplied(winery_id, limit=100)
        
        assert len(recommendations) == 1
        assert recommendations[0].recommendation_text == "Increase temperature"
        assert not recommendations[0].is_applied


@pytest.mark.integration
class TestRecommendationRepositoryListByPriority:
    """Test filtering recommendations by priority."""

    @pytest.mark.asyncio
    async def test_list_by_priority(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test listing recommendations by priority."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        for priority in [1, 2, 3, 4, 5]:
            rec = Recommendation(
                analysis_id=analysis.id,
                recommendation_template_id=template.id,
                recommendation_text=f"Recommendation {priority}",
                priority=priority,
                confidence=0.90,
                supporting_evidence_count=1
            )
            db_session.add(rec)
        await db_session.flush()
        
        high_priority = await recommendation_repository.list_by_priority(
            winery_id, min_priority=1, max_priority=2, limit=100
        )
        
        assert len(high_priority) == 2
        assert all(r.priority <= 2 for r in high_priority)


@pytest.mark.integration
class TestRecommendationRepositoryCountByTemplate:
    """Test counting recommendations by template."""

    @pytest.mark.asyncio
    async def test_count_by_template(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test counting recommendations by template."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        for i in range(3):
            rec = Recommendation(
                analysis_id=analysis.id,
                recommendation_template_id=template.id,
                recommendation_text=f"Recommendation {i}",
                priority=1,
                confidence=0.90,
                supporting_evidence_count=1
            )
            db_session.add(rec)
        await db_session.flush()
        
        count = await recommendation_repository.count_by_template(winery_id, template.id)
        
        assert count == 3


@pytest.mark.integration
class TestRecommendationRepositoryApplicationRate:
    """Test calculating application rate."""

    @pytest.mark.asyncio
    async def test_get_application_rate(self, recommendation_repository, db_session, winery_id, fermentation_id):
        """Test calculating application rate for a template."""
        analysis = Analysis(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            status=AnalysisStatus.COMPLETED.value,
            comparison_result={},
            confidence_level={}
        )
        db_session.add(analysis)
        await db_session.flush()
        
        template = RecommendationTemplate(
            code="TEMP_CONTROL",
            category=RecommendationCategory.TEMPERATURE_ADJUSTMENT.value,
            title="Temperature Control",
            description="Control temperature",
            applicable_anomaly_types=[AnomalyType.STUCK_FERMENTATION.value],
            priority_default=1
        )
        db_session.add(template)
        await db_session.flush()
        
        # 2 applied, 2 unapplied = 50% rate
        for i in range(2):
            rec = Recommendation(
                analysis_id=analysis.id,
                recommendation_template_id=template.id,
                recommendation_text=f"Applied {i}",
                priority=1,
                confidence=0.90,
                supporting_evidence_count=1,
                is_applied=True,
                applied_at=datetime.now(timezone.utc)
            )
            db_session.add(rec)
        
        for i in range(2):
            rec = Recommendation(
                analysis_id=analysis.id,
                recommendation_template_id=template.id,
                recommendation_text=f"Unapplied {i}",
                priority=1,
                confidence=0.90,
                supporting_evidence_count=1,
                is_applied=False
            )
            db_session.add(rec)
        await db_session.flush()
        
        rate = await recommendation_repository.get_application_rate_by_template(winery_id, template.id)
        
        assert abs(rate - 0.5) < 0.01  # 50% with tolerance

"""
Tests for RecommendationService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.recommendation_service import (
    RecommendationService,
)
from src.modules.analysis_engine.src.domain.enums.anomaly_type import AnomalyType
from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel


@pytest.fixture
def service(mock_async_session):
    return RecommendationService(session=mock_async_session)


class TestGenerateRecommendations:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_anomalies(self, service, winery_id):
        result = await service.generate_recommendations(
            winery_id=winery_id,
            analysis_id=uuid4(),
            anomalies=[],
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_empty_when_no_templates(self, service, winery_id, mock_async_session, anomaly_factory):
        # session returns no templates
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        anomaly = anomaly_factory(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        result = await service.generate_recommendations(
            winery_id=winery_id,
            analysis_id=uuid4(),
            anomalies=[anomaly],
        )
        assert result == []


class TestCalculatePriority:
    def test_critical_anomaly_has_high_priority(self, anomaly_factory):
        anomaly = anomaly_factory(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        template = MagicMock()
        template.effectiveness_score = 80
        priority = RecommendationService._calculate_priority(anomaly, template)
        assert priority >= 1000

    def test_info_anomaly_has_low_priority(self, anomaly_factory):
        anomaly = anomaly_factory(AnomalyType.UNUSUAL_DURATION, SeverityLevel.INFO)
        template = MagicMock()
        template.effectiveness_score = 50
        priority = RecommendationService._calculate_priority(anomaly, template)
        assert priority < 100

    def test_critical_priority_greater_than_warning(self, anomaly_factory):
        anomaly_critical = anomaly_factory(AnomalyType.STUCK_FERMENTATION, SeverityLevel.CRITICAL)
        anomaly_warning = anomaly_factory(AnomalyType.DENSITY_DROP_TOO_FAST, SeverityLevel.WARNING)
        template = MagicMock()
        template.effectiveness_score = 50
        p_critical = RecommendationService._calculate_priority(anomaly_critical, template)
        p_warning = RecommendationService._calculate_priority(anomaly_warning, template)
        assert p_critical > p_warning


class TestRankAndGetTop:
    @pytest.mark.asyncio
    async def test_rank_recommendations_sorts_by_priority(self, service):
        r1 = MagicMock()
        r1.priority = 100
        r2 = MagicMock()
        r2.priority = 1000
        ranked = await service.rank_recommendations([r1, r2])
        assert ranked[0].priority == 1000

    @pytest.mark.asyncio
    async def test_get_top_recommendations_limits_results(self, service):
        recs = [MagicMock(priority=i) for i in range(10)]
        top = await service.get_top_recommendations(recs, limit=3)
        assert len(top) == 3


class TestRecordRecommendationApplied:
    @pytest.mark.asyncio
    async def test_marks_recommendation_applied(self, service, mock_async_session):
        rec_mock = MagicMock()
        rec_mock.is_applied = False
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = rec_mock
        await service.record_recommendation_applied(recommendation_id=uuid4())
        assert rec_mock.is_applied is True

    @pytest.mark.asyncio
    async def test_handles_not_found_gracefully(self, service, mock_async_session):
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None
        # Should not raise
        await service.record_recommendation_applied(recommendation_id=uuid4())

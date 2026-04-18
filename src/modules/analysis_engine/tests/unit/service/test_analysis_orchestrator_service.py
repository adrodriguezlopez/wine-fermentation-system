"""
Tests for AnalysisOrchestratorService.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import (
    AnalysisOrchestratorService,
)
from src.shared.domain.errors import CrossWineryAccessDenied
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel


class TestCalculateConfidence:
    def test_zero_historical_returns_low_confidence(self):
        cl = AnalysisOrchestratorService._calculate_confidence(
            historical_count=0, anomaly_count=0, recommendation_count=0
        )
        assert cl.historical_data_confidence == 0.3

    def test_many_historical_returns_high_confidence(self):
        cl = AnalysisOrchestratorService._calculate_confidence(
            historical_count=10, anomaly_count=0, recommendation_count=0
        )
        assert cl.historical_data_confidence == 0.9

    def test_returns_confidence_level_instance(self):
        cl = AnalysisOrchestratorService._calculate_confidence(5, 1, 2)
        assert isinstance(cl, ConfidenceLevel)

    def test_overall_confidence_within_range(self):
        cl = AnalysisOrchestratorService._calculate_confidence(5, 2, 3)
        assert 0.0 <= cl.overall_confidence <= 1.0

    def test_anomaly_count_affects_detection_confidence(self):
        cl_1 = AnalysisOrchestratorService._calculate_confidence(5, 1, 2)
        cl_many = AnalysisOrchestratorService._calculate_confidence(5, 10, 2)
        assert cl_many.detection_algorithm_confidence < cl_1.detection_algorithm_confidence

    def test_sample_size_stored_correctly(self):
        cl = AnalysisOrchestratorService._calculate_confidence(7, 1, 1)
        assert cl.sample_size == 7

    def test_anomaly_count_stored_correctly(self):
        cl = AnalysisOrchestratorService._calculate_confidence(5, 3, 2)
        assert cl.anomalies_detected == 3

    def test_recommendation_count_stored_correctly(self):
        cl = AnalysisOrchestratorService._calculate_confidence(5, 1, 4)
        assert cl.recommendations_generated == 4


class TestGetAnalysis:
    @pytest.mark.asyncio
    async def test_returns_none_when_not_found(self, mock_async_session, threshold_config):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session, threshold_config=threshold_config)
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = None
        result = await orchestrator.get_analysis(analysis_id=uuid4(), winery_id=uuid4())
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_analysis_for_correct_winery(self, mock_async_session, winery_id, threshold_config):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session, threshold_config=threshold_config)
        analysis = MagicMock()
        analysis.winery_id = winery_id
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = analysis
        result = await orchestrator.get_analysis(analysis_id=uuid4(), winery_id=winery_id)
        assert result is analysis

    @pytest.mark.asyncio
    async def test_raises_for_wrong_winery(self, mock_async_session, winery_id, threshold_config):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session, threshold_config=threshold_config)
        analysis = MagicMock()
        analysis.winery_id = uuid4()  # Different winery
        mock_async_session.execute.return_value.scalar_one_or_none.return_value = analysis
        with pytest.raises(CrossWineryAccessDenied, match="belongs to winery"):
            await orchestrator.get_analysis(analysis_id=uuid4(), winery_id=winery_id)


class TestGetFermentationAnalyses:
    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_analyses(self, mock_async_session, winery_id, fermentation_id, threshold_config):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session, threshold_config=threshold_config)
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = []
        result = await orchestrator.get_fermentation_analyses(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
        )
        assert result == []

    @pytest.mark.asyncio
    async def test_returns_list_of_analyses(self, mock_async_session, winery_id, fermentation_id, threshold_config):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session, threshold_config=threshold_config)
        analyses = [MagicMock(), MagicMock()]
        mock_async_session.execute.return_value.scalars.return_value.all.return_value = analyses
        result = await orchestrator.get_fermentation_analyses(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
        )
        assert len(result) == 2


class TestExecuteAnalysis:
    @pytest.mark.asyncio
    @pytest.mark.skip(reason="covered by integration tests in tests/integration/service/test_analysis_orchestrator_integration.py — requires real PostgreSQL for cross-module Fermentation query via ComparisonService")
    async def test_execute_analysis_completes_status(self, mock_async_session, winery_id, fermentation_id):
        orchestrator = AnalysisOrchestratorService(session=mock_async_session)
        result = await orchestrator.execute_analysis(
            winery_id=winery_id,
            fermentation_id=fermentation_id,
            current_density=50.0,
            temperature_celsius=25.0,
            variety="Merlot",
        )
        assert result.status == AnalysisStatus.COMPLETED.value

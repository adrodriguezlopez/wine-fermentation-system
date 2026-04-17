"""
Integration tests for AnalysisOrchestratorService.execute_analysis().

These tests replace the 1 skipped unit test in
``tests/unit/service/test_analysis_orchestrator_service.py``.  They run against
a real PostgreSQL instance (localhost:5433/wine_fermentation_test) so that
ComparisonService can execute its cross-module Fermentation query without
the lazy-import error that prevents the unit test from running in isolation.

Prerequisites:
    docker compose -f docker-compose.inttest.yml up --wait

Skipped unit test being replaced:
    TestExecuteAnalysis::test_execute_analysis_completes_status

Design notes:
- execute_analysis() creates an Analysis in-memory (never persists it — the
  orchestrator returns it but does not call session.add/commit).
- ComparisonService will find zero similar fermentations (no Fermentation rows
  match the UUID winery_id passed in), so the analysis completes with an empty
  comparison result.
- RecommendationService is also called; with no anomalies detected it returns
  an empty list, so no RecommendationTemplate rows are needed.
- The returned Analysis.status should be COMPLETED (not FAILED) when the full
  pipeline runs without an unhandled exception.
"""
import pytest
from uuid import uuid4

from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import (
    AnalysisOrchestratorService,
)
from src.modules.analysis_engine.src.domain.entities.analysis import Analysis
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus
from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel

pytestmark = pytest.mark.integration


class TestExecuteAnalysisIntegration:
    """
    Integration coverage for AnalysisOrchestratorService.execute_analysis().

    Replaces:
        TestExecuteAnalysis::test_execute_analysis_completes_status
    """

    @pytest.mark.asyncio
    async def test_execute_analysis_returns_completed_status(self, db_session):
        """
        execute_analysis() should return an Analysis whose status is COMPLETED
        when the full pipeline (comparison → anomaly detection → recommendations)
        runs without error.

        With no matching Fermentation rows for the UUID winery_id, the comparison
        step finds zero similar fermentations — a valid empty-result scenario.
        Anomaly detection with a normal density reading raises no anomalies, so
        no RecommendationTemplate rows are needed.
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.050,          # Normal mid-fermentation density
            temperature_celsius=22.0,       # Normal temperature
            variety="Merlot",
            starting_brix=None,
            days_fermenting=5.0,
        )

        assert result.status == AnalysisStatus.COMPLETED.value

    @pytest.mark.asyncio
    async def test_execute_analysis_returns_analysis_instance(self, db_session):
        """
        execute_analysis() must return an Analysis object (aggregate root).
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.080,
            temperature_celsius=18.0,
            variety="Pinot Noir",
        )

        assert isinstance(result, Analysis)

    @pytest.mark.asyncio
    async def test_execute_analysis_comparison_result_stored(self, db_session):
        """
        After execute_analysis(), the returned Analysis must have a non-empty
        comparison_result dict (populated by ComparisonService.build_comparison_result).
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.070,
            temperature_celsius=20.0,
            variety="Cabernet Sauvignon",
        )

        assert result.comparison_result is not None
        assert isinstance(result.comparison_result, dict)
        # ComparisonResult.to_dict() always includes similar_fermentation_count
        assert "similar_fermentation_count" in result.comparison_result

    @pytest.mark.asyncio
    async def test_execute_analysis_confidence_level_stored(self, db_session):
        """
        After execute_analysis(), the returned Analysis must have a non-empty
        confidence_level dict (populated by _calculate_confidence).
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.060,
            temperature_celsius=21.0,
            variety="Chardonnay",
        )

        assert result.confidence_level is not None
        assert isinstance(result.confidence_level, dict)
        assert "overall_confidence" in result.confidence_level

    @pytest.mark.asyncio
    async def test_execute_analysis_zero_historical_samples_when_no_matches(self, db_session):
        """
        With a UUID winery_id that has no matching Fermentation rows,
        historical_samples_count should be 0.
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.090,
            temperature_celsius=23.0,
            variety="Syrah",
        )

        assert result.historical_samples_count == 0

    @pytest.mark.asyncio
    async def test_execute_analysis_with_protocol_compliance_score(self, db_session):
        """
        execute_analysis() with a protocol_compliance_score provided should
        still complete successfully (ADR-037 boost path).  The returned status
        must be COMPLETED and overall_confidence must be within [0.0, 1.0].
        """
        orchestrator = AnalysisOrchestratorService(session=db_session)

        result = await orchestrator.execute_analysis(
            winery_id=uuid4(),
            fermentation_id=uuid4(),
            current_density=1.055,
            temperature_celsius=19.5,
            variety="Grenache",
            protocol_compliance_score=85.0,
        )

        assert result.status == AnalysisStatus.COMPLETED.value
        overall = result.confidence_level.get("overall_confidence", -1)
        assert 0.0 <= overall <= 1.0

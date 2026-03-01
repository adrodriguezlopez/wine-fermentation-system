"""
Unit tests for Analysis Engine API Layer.

Tests analysis_router.py and recommendation_router.py endpoints with mocked
dependencies following the same pattern as fermentation module tests.

Endpoints tested:
- POST /api/v1/analyses                              → trigger_analysis
- GET  /api/v1/analyses/{analysis_id}                → get_analysis
- GET  /api/v1/analyses/fermentation/{id}             → list_fermentation_analyses
- GET  /api/v1/recommendations/{id}                   → get_recommendation
- PUT  /api/v1/recommendations/{id}/apply             → apply_recommendation

Following ADR-028 Testing Strategy, ADR-006 API Layer Design.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4
from datetime import datetime, timezone

# Add project root and src to path (same pattern as other analysis_engine tests)
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
src_path = project_root / "src"
for p in [str(project_root), str(src_path)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.shared.domain.errors import CrossWineryAccessDenied

from src.modules.analysis_engine.src.api.routers.analysis_router import (
    trigger_analysis,
    get_analysis,
    list_fermentation_analyses,
)
from src.modules.analysis_engine.src.api.routers.recommendation_router import (
    get_recommendation,
    apply_recommendation,
)
from src.modules.analysis_engine.src.api.schemas.requests.analysis_requests import (
    AnalysisCreateRequest,
    DensityReadingRequest,
    RecommendationApplyRequest,
)
from src.modules.analysis_engine.src.api.schemas.responses.analysis_responses import (
    AnalysisResponse,
    AnalysisSummaryResponse,
    AnomalyResponse,
    RecommendationResponse,
)
from src.modules.analysis_engine.src.domain.enums.analysis_status import AnalysisStatus


# ==============================================================================
# Fixtures
# ==============================================================================

WINERY_ID = uuid4()
USER_ID = 42
ANALYSIS_ID = uuid4()
FERMENTATION_ID = uuid4()
RECOMMENDATION_ID = uuid4()
ANOMALY_ID = uuid4()
TEMPLATE_ID = uuid4()


@pytest.fixture
def winemaker_user():
    """Authenticated winemaker user context."""
    return UserContext(
        user_id=USER_ID,
        email="winemaker@test.com",
        role=UserRole.WINEMAKER,
        winery_id=WINERY_ID,
    )


@pytest.fixture
def analysis_create_request():
    """Valid analysis creation request."""
    return AnalysisCreateRequest(
        fermentation_id=FERMENTATION_ID,
        current_density=1050.5,
        temperature_celsius=22.0,
        variety="Cabernet Sauvignon",
        starting_brix=24.0,
        days_fermenting=5.0,
        previous_densities=[
            DensityReadingRequest(
                timestamp=datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc),
                density=1080.0,
            ),
            DensityReadingRequest(
                timestamp=datetime(2024, 1, 2, 8, 0, tzinfo=timezone.utc),
                density=1065.0,
            ),
        ],
    )


def make_mock_analysis(
    analysis_id: UUID = ANALYSIS_ID,
    fermentation_id: UUID = FERMENTATION_ID,
    winery_id: UUID = WINERY_ID,
    status: str = "COMPLETE",
    anomalies=None,
    recommendations=None,
):
    """Build a mock Analysis ORM entity."""
    mock = MagicMock()
    mock.id = analysis_id
    mock.fermentation_id = fermentation_id
    mock.winery_id = winery_id
    mock.status = status
    mock.analyzed_at = datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc)
    mock.comparison_result = {"similar_count": 3, "average_duration_days": 14.0}
    mock.confidence_level = {"level": "MEDIUM", "historical_samples_count": 3, "similarity_score": 75.0, "explanation": "3 similar fermentations"}
    mock.historical_samples_count = 3
    mock.anomalies = anomalies or []
    mock.recommendations = recommendations or []
    return mock


def make_mock_recommendation(
    rec_id: UUID = RECOMMENDATION_ID,
    analysis_id: UUID = ANALYSIS_ID,
    is_applied: bool = False,
):
    """Build a mock Recommendation ORM entity."""
    mock = MagicMock()
    mock.id = rec_id
    mock.analysis_id = analysis_id
    mock.anomaly_id = None
    mock.recommendation_template_id = TEMPLATE_ID
    mock.recommendation_text = "Add 50g/hL DAP nutrients to fermentation"
    mock.priority = 1
    mock.confidence = 0.85
    mock.supporting_evidence_count = 5
    mock.is_applied = is_applied
    mock.applied_at = None
    return mock


@pytest.fixture
def mock_orchestrator():
    """Mock AnalysisOrchestratorService."""
    svc = MagicMock()
    svc.execute_analysis = AsyncMock()
    svc.get_analysis = AsyncMock()
    svc.get_fermentation_analyses = AsyncMock()
    return svc


@pytest.fixture
def mock_recommendation_repo():
    """Mock RecommendationRepository."""
    repo = MagicMock()
    repo.get_by_id = AsyncMock()
    return repo


@pytest.fixture
def mock_session():
    """Mock AsyncSession for commit/refresh."""
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    return session


# ==============================================================================
# Tests: POST /api/v1/analyses  (trigger_analysis)
# ==============================================================================

class TestTriggerAnalysis:
    """Tests for the trigger_analysis endpoint."""

    @pytest.mark.asyncio
    async def test_trigger_analysis_success(
        self, winemaker_user, analysis_create_request, mock_orchestrator
    ):
        """Should return 201 with AnalysisResponse when analysis succeeds."""
        mock_analysis = make_mock_analysis()
        mock_orchestrator.execute_analysis.return_value = mock_analysis

        result = await trigger_analysis(
            request=analysis_create_request,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        assert isinstance(result, AnalysisResponse)
        assert result.id == ANALYSIS_ID
        assert result.fermentation_id == FERMENTATION_ID
        assert result.winery_id == WINERY_ID
        assert result.status == "COMPLETE"

    @pytest.mark.asyncio
    async def test_trigger_analysis_passes_winery_id(
        self, winemaker_user, analysis_create_request, mock_orchestrator
    ):
        """Should pass winery_id from user context (not from request) to service."""
        mock_orchestrator.execute_analysis.return_value = make_mock_analysis()

        await trigger_analysis(
            request=analysis_create_request,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        call_kwargs = mock_orchestrator.execute_analysis.call_args.kwargs
        assert call_kwargs["winery_id"] == WINERY_ID
        assert call_kwargs["fermentation_id"] == FERMENTATION_ID

    @pytest.mark.asyncio
    async def test_trigger_analysis_converts_density_readings(
        self, winemaker_user, analysis_create_request, mock_orchestrator
    ):
        """Should convert DensityReadingRequest list to (datetime, float) tuples."""
        mock_orchestrator.execute_analysis.return_value = make_mock_analysis()

        await trigger_analysis(
            request=analysis_create_request,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        call_kwargs = mock_orchestrator.execute_analysis.call_args.kwargs
        previous_densities = call_kwargs["previous_densities"]
        assert previous_densities is not None
        assert len(previous_densities) == 2
        # Each element is a (datetime, float) tuple
        ts, density = previous_densities[0]
        assert isinstance(ts, datetime)
        assert isinstance(density, float)

    @pytest.mark.asyncio
    async def test_trigger_analysis_no_previous_densities(
        self, winemaker_user, mock_orchestrator
    ):
        """Should pass None for previous_densities when not provided."""
        request = AnalysisCreateRequest(
            fermentation_id=FERMENTATION_ID,
            current_density=1050.0,
            temperature_celsius=22.0,
            variety="Pinot Noir",
        )
        mock_orchestrator.execute_analysis.return_value = make_mock_analysis()

        await trigger_analysis(
            request=request,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        call_kwargs = mock_orchestrator.execute_analysis.call_args.kwargs
        assert call_kwargs["previous_densities"] is None

    @pytest.mark.asyncio
    async def test_trigger_analysis_with_anomalies_and_recommendations(
        self, winemaker_user, analysis_create_request, mock_orchestrator
    ):
        """Should include nested anomalies and recommendations in response."""
        mock_anomaly = MagicMock()
        mock_anomaly.id = ANOMALY_ID
        mock_anomaly.analysis_id = ANALYSIS_ID
        mock_anomaly.sample_id = None
        mock_anomaly.anomaly_type = "STUCK_FERMENTATION"
        mock_anomaly.severity = "CRITICAL"
        mock_anomaly.description = "Fermentation appears stuck"
        mock_anomaly.deviation_score = {"score": 0.95, "threshold": 0.5}
        mock_anomaly.is_resolved = False
        mock_anomaly.detected_at = datetime(2024, 1, 3, 12, 0, tzinfo=timezone.utc)
        mock_anomaly.resolved_at = None

        mock_rec = make_mock_recommendation()

        mock_analysis = make_mock_analysis(
            anomalies=[mock_anomaly],
            recommendations=[mock_rec],
        )
        mock_orchestrator.execute_analysis.return_value = mock_analysis

        result = await trigger_analysis(
            request=analysis_create_request,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        assert len(result.anomalies) == 1
        assert result.anomalies[0].anomaly_type == "STUCK_FERMENTATION"
        assert result.anomalies[0].severity == "CRITICAL"
        assert len(result.recommendations) == 1
        assert result.recommendations[0].priority == 1

    @pytest.mark.asyncio
    async def test_trigger_analysis_service_error_propagates(
        self, winemaker_user, analysis_create_request, mock_orchestrator
    ):
        """Should propagate CrossWineryAccessDenied as HTTP 403."""
        from fastapi import HTTPException
        mock_orchestrator.execute_analysis.side_effect = CrossWineryAccessDenied(
            "Access denied"
        )

        with pytest.raises(HTTPException) as exc_info:
            await trigger_analysis(
                request=analysis_create_request,
                current_user=winemaker_user,
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 403


# ==============================================================================
# Tests: GET /api/v1/analyses/{analysis_id}  (get_analysis)
# ==============================================================================

class TestGetAnalysis:
    """Tests for the get_analysis endpoint."""

    @pytest.mark.asyncio
    async def test_get_analysis_success(self, winemaker_user, mock_orchestrator):
        """Should return AnalysisResponse when analysis is found."""
        mock_analysis = make_mock_analysis()
        mock_orchestrator.get_analysis.return_value = mock_analysis

        result = await get_analysis(
            analysis_id=ANALYSIS_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        assert isinstance(result, AnalysisResponse)
        assert result.id == ANALYSIS_ID

    @pytest.mark.asyncio
    async def test_get_analysis_not_found_raises_404(self, winemaker_user, mock_orchestrator):
        """Should raise HTTP 404 when analysis is not found."""
        from fastapi import HTTPException
        mock_orchestrator.get_analysis.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_analysis(
                analysis_id=ANALYSIS_ID,
                current_user=winemaker_user,
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 404
        assert str(ANALYSIS_ID) in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_analysis_passes_winery_id_for_security(
        self, winemaker_user, mock_orchestrator
    ):
        """Should pass winery_id from user context to orchestrator for multi-tenancy check."""
        mock_orchestrator.get_analysis.return_value = make_mock_analysis()

        await get_analysis(
            analysis_id=ANALYSIS_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
        )

        call_kwargs = mock_orchestrator.get_analysis.call_args.kwargs
        assert call_kwargs["winery_id"] == WINERY_ID
        assert call_kwargs["analysis_id"] == ANALYSIS_ID

    @pytest.mark.asyncio
    async def test_get_analysis_cross_winery_raises_403(
        self, winemaker_user, mock_orchestrator
    ):
        """Should propagate CrossWineryAccessDenied as HTTP 403."""
        from fastapi import HTTPException
        mock_orchestrator.get_analysis.side_effect = CrossWineryAccessDenied(
            "Access denied"
        )

        with pytest.raises(HTTPException) as exc_info:
            await get_analysis(
                analysis_id=ANALYSIS_ID,
                current_user=winemaker_user,
                orchestrator=mock_orchestrator,
            )

        assert exc_info.value.status_code == 403


# ==============================================================================
# Tests: GET /api/v1/analyses/fermentation/{id}  (list_fermentation_analyses)
# ==============================================================================

class TestListFermentationAnalyses:
    """Tests for the list_fermentation_analyses endpoint."""

    @pytest.mark.asyncio
    async def test_list_analyses_returns_summaries(
        self, winemaker_user, mock_orchestrator
    ):
        """Should return a list of AnalysisSummaryResponse."""
        mock_orchestrator.get_fermentation_analyses.return_value = [
            make_mock_analysis(analysis_id=uuid4()),
            make_mock_analysis(analysis_id=uuid4()),
        ]

        result = await list_fermentation_analyses(
            fermentation_id=FERMENTATION_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
            limit=10,
        )

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(r, AnalysisSummaryResponse) for r in result)

    @pytest.mark.asyncio
    async def test_list_analyses_empty_returns_empty_list(
        self, winemaker_user, mock_orchestrator
    ):
        """Should return empty list when no analyses exist."""
        mock_orchestrator.get_fermentation_analyses.return_value = []

        result = await list_fermentation_analyses(
            fermentation_id=FERMENTATION_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
            limit=10,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_list_analyses_passes_limit(
        self, winemaker_user, mock_orchestrator
    ):
        """Should pass the limit parameter to the orchestrator."""
        mock_orchestrator.get_fermentation_analyses.return_value = []

        await list_fermentation_analyses(
            fermentation_id=FERMENTATION_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
            limit=5,
        )

        call_kwargs = mock_orchestrator.get_fermentation_analyses.call_args.kwargs
        assert call_kwargs["limit"] == 5

    @pytest.mark.asyncio
    async def test_list_analyses_passes_winery_id(
        self, winemaker_user, mock_orchestrator
    ):
        """Should pass winery_id from user context for multi-tenancy."""
        mock_orchestrator.get_fermentation_analyses.return_value = []

        await list_fermentation_analyses(
            fermentation_id=FERMENTATION_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
            limit=10,
        )

        call_kwargs = mock_orchestrator.get_fermentation_analyses.call_args.kwargs
        assert call_kwargs["winery_id"] == WINERY_ID
        assert call_kwargs["fermentation_id"] == FERMENTATION_ID

    @pytest.mark.asyncio
    async def test_list_analyses_summary_counts_anomalies_and_recs(
        self, winemaker_user, mock_orchestrator
    ):
        """AnalysisSummaryResponse should include anomaly_count and recommendation_count."""
        mock_anomaly = MagicMock()
        mock_rec = MagicMock()
        mock_analysis = make_mock_analysis(
            anomalies=[mock_anomaly, mock_anomaly],
            recommendations=[mock_rec],
        )
        mock_orchestrator.get_fermentation_analyses.return_value = [mock_analysis]

        result = await list_fermentation_analyses(
            fermentation_id=FERMENTATION_ID,
            current_user=winemaker_user,
            orchestrator=mock_orchestrator,
            limit=10,
        )

        assert result[0].anomaly_count == 2
        assert result[0].recommendation_count == 1


# ==============================================================================
# Tests: GET /api/v1/recommendations/{id}  (get_recommendation)
# ==============================================================================

class TestGetRecommendation:
    """Tests for the get_recommendation endpoint."""

    @pytest.mark.asyncio
    async def test_get_recommendation_success(
        self, winemaker_user, mock_recommendation_repo
    ):
        """Should return RecommendationResponse when found."""
        mock_rec = make_mock_recommendation()
        mock_recommendation_repo.get_by_id.return_value = mock_rec

        result = await get_recommendation(
            recommendation_id=RECOMMENDATION_ID,
            current_user=winemaker_user,
            repo=mock_recommendation_repo,
        )

        assert isinstance(result, RecommendationResponse)
        assert result.id == RECOMMENDATION_ID

    @pytest.mark.asyncio
    async def test_get_recommendation_not_found_raises_404(
        self, winemaker_user, mock_recommendation_repo
    ):
        """Should raise HTTP 404 when recommendation is not found."""
        from fastapi import HTTPException
        mock_recommendation_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await get_recommendation(
                recommendation_id=RECOMMENDATION_ID,
                current_user=winemaker_user,
                repo=mock_recommendation_repo,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_get_recommendation_returns_correct_data(
        self, winemaker_user, mock_recommendation_repo
    ):
        """Should return correct recommendation data."""
        mock_rec = make_mock_recommendation(is_applied=False)
        mock_recommendation_repo.get_by_id.return_value = mock_rec

        result = await get_recommendation(
            recommendation_id=RECOMMENDATION_ID,
            current_user=winemaker_user,
            repo=mock_recommendation_repo,
        )

        assert result.is_applied is False
        assert result.priority == 1
        assert result.confidence == 0.85
        assert "DAP" in result.recommendation_text


# ==============================================================================
# Tests: PUT /api/v1/recommendations/{id}/apply  (apply_recommendation)
# ==============================================================================

class TestApplyRecommendation:
    """Tests for the apply_recommendation endpoint."""

    @pytest.mark.asyncio
    async def test_apply_recommendation_success(
        self, winemaker_user, mock_recommendation_repo, mock_session
    ):
        """Should mark recommendation as applied and return updated DTO."""
        mock_rec = make_mock_recommendation(is_applied=False)
        mock_rec.apply = MagicMock()  # Sync method on entity
        # After apply() is called, simulate applied state for refresh
        mock_session.refresh = AsyncMock(
            side_effect=lambda rec: setattr(rec, "is_applied", True) or None
        )
        mock_recommendation_repo.get_by_id.return_value = mock_rec

        apply_request = RecommendationApplyRequest(
            notes="Applied as instructed at 14:30"
        )

        result = await apply_recommendation(
            recommendation_id=RECOMMENDATION_ID,
            request=apply_request,
            current_user=winemaker_user,
            repo=mock_recommendation_repo,
            session=mock_session,
        )

        # Verify entity.apply() was called
        mock_rec.apply.assert_called_once()

        # Verify session operations
        mock_session.add.assert_called_once_with(mock_rec)
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once_with(mock_rec)

        assert isinstance(result, RecommendationResponse)

    @pytest.mark.asyncio
    async def test_apply_recommendation_not_found_raises_404(
        self, winemaker_user, mock_recommendation_repo, mock_session
    ):
        """Should raise HTTP 404 when recommendation does not exist."""
        from fastapi import HTTPException
        mock_recommendation_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await apply_recommendation(
                recommendation_id=RECOMMENDATION_ID,
                request=RecommendationApplyRequest(),
                current_user=winemaker_user,
                repo=mock_recommendation_repo,
                session=mock_session,
            )

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_apply_already_applied_raises_409(
        self, winemaker_user, mock_recommendation_repo, mock_session
    ):
        """Should raise HTTP 409 Conflict when recommendation is already applied."""
        from fastapi import HTTPException
        mock_rec = make_mock_recommendation(is_applied=True)
        mock_recommendation_repo.get_by_id.return_value = mock_rec

        with pytest.raises(HTTPException) as exc_info:
            await apply_recommendation(
                recommendation_id=RECOMMENDATION_ID,
                request=RecommendationApplyRequest(),
                current_user=winemaker_user,
                repo=mock_recommendation_repo,
                session=mock_session,
            )

        assert exc_info.value.status_code == 409

    @pytest.mark.asyncio
    async def test_apply_recommendation_no_commit_if_not_found(
        self, winemaker_user, mock_recommendation_repo, mock_session
    ):
        """Should not call session.commit() when recommendation is not found."""
        from fastapi import HTTPException
        mock_recommendation_repo.get_by_id.return_value = None

        with pytest.raises(HTTPException):
            await apply_recommendation(
                recommendation_id=RECOMMENDATION_ID,
                request=RecommendationApplyRequest(),
                current_user=winemaker_user,
                repo=mock_recommendation_repo,
                session=mock_session,
            )

        mock_session.commit.assert_not_awaited()


# ==============================================================================
# Tests: Request schema validation
# ==============================================================================

class TestAnalysisCreateRequestValidation:
    """Tests for AnalysisCreateRequest Pydantic validation."""

    def test_valid_request_passes(self):
        """Should create request with valid data."""
        req = AnalysisCreateRequest(
            fermentation_id=uuid4(),
            current_density=1050.0,
            temperature_celsius=22.0,
            variety="Malbec",
        )
        assert req.variety == "Malbec"
        assert req.days_fermenting == 0.0

    def test_density_out_of_range_raises(self):
        """Should reject current_density outside valid range."""
        with pytest.raises(Exception):
            AnalysisCreateRequest(
                fermentation_id=uuid4(),
                current_density=500.0,  # Too low (< 900)
                temperature_celsius=22.0,
                variety="Malbec",
            )

    def test_temperature_too_high_raises(self):
        """Should reject temperature above 60°C."""
        with pytest.raises(Exception):
            AnalysisCreateRequest(
                fermentation_id=uuid4(),
                current_density=1050.0,
                temperature_celsius=80.0,  # Too high (> 60)
                variety="Malbec",
            )

    def test_variety_stripped(self):
        """Should strip whitespace from variety."""
        req = AnalysisCreateRequest(
            fermentation_id=uuid4(),
            current_density=1050.0,
            temperature_celsius=22.0,
            variety="  Chardonnay  ",
        )
        assert req.variety == "Chardonnay"

    def test_days_fermenting_defaults_to_zero(self):
        """Should default days_fermenting to 0.0 when not provided."""
        req = AnalysisCreateRequest(
            fermentation_id=uuid4(),
            current_density=1050.0,
            temperature_celsius=22.0,
            variety="Merlot",
        )
        assert req.days_fermenting == 0.0

    def test_optional_fields_default_to_none(self):
        """Optional fields should default to None."""
        req = AnalysisCreateRequest(
            fermentation_id=uuid4(),
            current_density=1050.0,
            temperature_celsius=22.0,
            variety="Syrah",
        )
        assert req.fruit_origin_id is None
        assert req.starting_brix is None
        assert req.previous_densities is None


# ==============================================================================
# Tests: Response schema helpers
# ==============================================================================

class TestAnalysisResponseFromOrmEntity:
    """Tests for AnalysisResponse.from_orm_entity classmethod."""

    def test_from_orm_entity_basic(self):
        """Should build AnalysisResponse from mock ORM entity."""
        mock_entity = make_mock_analysis()
        response = AnalysisResponse.from_orm_entity(mock_entity)

        assert response.id == ANALYSIS_ID
        assert response.fermentation_id == FERMENTATION_ID
        assert response.winery_id == WINERY_ID
        assert response.status == "COMPLETE"
        assert response.historical_samples_count == 3

    def test_from_orm_entity_empty_relationships(self):
        """Should return empty lists when no anomalies/recommendations."""
        mock_entity = make_mock_analysis(anomalies=[], recommendations=[])
        response = AnalysisResponse.from_orm_entity(mock_entity)

        assert response.anomalies == []
        assert response.recommendations == []

    def test_from_orm_entity_relationship_access_error_handled(self):
        """Should gracefully handle lazy-load errors on relationships."""
        mock_entity = MagicMock()
        mock_entity.id = ANALYSIS_ID
        mock_entity.fermentation_id = FERMENTATION_ID
        mock_entity.winery_id = WINERY_ID
        mock_entity.status = "FAILED"
        mock_entity.analyzed_at = datetime(2024, 1, 3, tzinfo=timezone.utc)
        mock_entity.comparison_result = {}
        mock_entity.confidence_level = {}
        mock_entity.historical_samples_count = 0
        # Simulate lazy-load failure
        type(mock_entity).anomalies = property(lambda self: (_ for _ in ()).throw(Exception("Not loaded")))
        type(mock_entity).recommendations = property(lambda self: (_ for _ in ()).throw(Exception("Not loaded")))

        response = AnalysisResponse.from_orm_entity(mock_entity)

        # Should not raise, fall back to empty lists
        assert response.anomalies == []
        assert response.recommendations == []

"""
Analysis Router - REST API endpoints for fermentation analysis.

Implements analysis trigger and retrieval with:
- JWT authentication (require_winemaker)
- Multi-tenancy enforcement (winery_id from user context)
- Request/response validation via Pydantic

Endpoints:
    POST   /api/v1/analyses                          → trigger new analysis
    GET    /api/v1/analyses/{analysis_id}            → get analysis by ID
    GET    /api/v1/analyses/fermentation/{fermentation_id} → list analyses for a fermentation

Following ADR-006 API Layer Design and ADR-020 Analysis Engine Architecture.
"""

from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker

from src.modules.analysis_engine.src.api.dependencies import get_analysis_orchestrator
from src.modules.analysis_engine.src.api.error_handlers import handle_service_errors
from src.modules.analysis_engine.src.api.schemas.requests.analysis_requests import AnalysisCreateRequest
from src.modules.analysis_engine.src.api.schemas.responses.analysis_responses import (
    AnalysisResponse,
    AnalysisSummaryResponse,
)
from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import (
    AnalysisOrchestratorService,
)

router = APIRouter(
    prefix="/analyses",
    tags=["analyses"],
)


@router.post(
    "",
    response_model=AnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger a fermentation analysis",
    description=(
        "Runs the full analysis pipeline for a fermentation: "
        "historical comparison → anomaly detection → recommendations. "
        "Requires WINEMAKER or ADMIN role."
    ),
)
@handle_service_errors
async def trigger_analysis(
    request: AnalysisCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    orchestrator: Annotated[AnalysisOrchestratorService, Depends(get_analysis_orchestrator)],
) -> AnalysisResponse:
    """
    Trigger a new fermentation analysis.

    The analysis engine:
    1. Finds similar historical fermentations (ComparisonService)
    2. Detects anomalies in current readings (AnomalyDetectionService)
    3. Generates actionable recommendations (RecommendationService)

    Args:
        request: Current fermentation readings and metadata
        current_user: Authenticated user (provides winery_id for multi-tenancy)
        orchestrator: Analysis orchestrator service

    Returns:
        AnalysisResponse: Complete analysis with anomalies and recommendations

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Insufficient permissions or cross-winery access attempt
        HTTP 422: Invalid request data
        HTTP 500: Analysis pipeline failure
    """
    # Convert density readings to (datetime, float) tuples expected by service
    previous_densities = None
    if request.previous_densities:
        previous_densities = [
            (reading.timestamp, reading.density)
            for reading in request.previous_densities
        ]

    analysis = await orchestrator.execute_analysis(
        winery_id=current_user.winery_id,
        fermentation_id=request.fermentation_id,
        current_density=request.current_density,
        temperature_celsius=request.temperature_celsius,
        variety=request.variety,
        fruit_origin_id=request.fruit_origin_id,
        starting_brix=request.starting_brix,
        days_fermenting=request.days_fermenting,
        previous_densities=previous_densities,
        protocol_compliance_score=request.protocol_compliance_score,  # ADR-037 boost
    )

    return AnalysisResponse.from_orm_entity(analysis)


@router.get(
    "/{analysis_id}",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Get analysis by ID",
    description="Retrieve a specific analysis with all anomalies and recommendations. Multi-tenancy enforced.",
)
@handle_service_errors
async def get_analysis(
    analysis_id: UUID,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    orchestrator: Annotated[AnalysisOrchestratorService, Depends(get_analysis_orchestrator)],
) -> AnalysisResponse:
    """
    Retrieve an analysis by ID.

    Args:
        analysis_id: UUID of the analysis
        current_user: Authenticated user (winery_id used for security check)
        orchestrator: Analysis orchestrator service

    Returns:
        AnalysisResponse: Full analysis with anomalies and recommendations

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Analysis belongs to a different winery
        HTTP 404: Analysis not found
    """
    analysis = await orchestrator.get_analysis(
        analysis_id=analysis_id,
        winery_id=current_user.winery_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    return AnalysisResponse.from_orm_entity(analysis)


@router.get(
    "/fermentation/{fermentation_id}",
    response_model=List[AnalysisSummaryResponse],
    status_code=status.HTTP_200_OK,
    summary="List analyses for a fermentation",
    description="Get the analysis history for a fermentation. Returns most recent first. Multi-tenancy enforced.",
)
@handle_service_errors
async def list_fermentation_analyses(
    fermentation_id: UUID,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    orchestrator: Annotated[AnalysisOrchestratorService, Depends(get_analysis_orchestrator)],
    limit: int = Query(10, ge=1, le=50, description="Maximum number of analyses to return"),
) -> List[AnalysisSummaryResponse]:
    """
    List analyses for a fermentation (most recent first).

    Args:
        fermentation_id: UUID of the fermentation
        current_user: Authenticated user (winery_id for multi-tenancy)
        orchestrator: Analysis orchestrator service
        limit: Max results to return (1-50, default 10)

    Returns:
        List of AnalysisSummaryResponse (lightweight, no nested relationships)

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Cross-winery access attempt
    """
    analyses = await orchestrator.get_fermentation_analyses(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        limit=limit,
    )

    return [
        AnalysisSummaryResponse(
            id=a.id,
            fermentation_id=a.fermentation_id,
            status=a.status,
            analyzed_at=a.analyzed_at,
            historical_samples_count=a.historical_samples_count or 0,
            anomaly_count=len(a.anomalies) if a.anomalies else 0,
            recommendation_count=len(a.recommendations) if a.recommendations else 0,
        )
        for a in analyses
    ]

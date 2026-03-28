"""
Recommendation Router - REST API endpoints for managing recommendations.

Endpoints:
    PUT    /api/v1/recommendations/{recommendation_id}/apply  → mark recommendation as applied
    GET    /api/v1/recommendations/{recommendation_id}        → get recommendation by ID

The winemaker confirms they've applied a recommendation so the system
can track effectiveness and improve future suggestions.

Following ADR-006 API Layer Design and ADR-020 Analysis Engine Architecture.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker
from src.shared.infra.database.fastapi_session import get_db_session

from src.modules.analysis_engine.src.api.dependencies import get_recommendation_repository
from src.modules.analysis_engine.src.api.error_handlers import handle_service_errors
from src.modules.analysis_engine.src.api.schemas.requests.analysis_requests import RecommendationApplyRequest
from src.modules.analysis_engine.src.api.schemas.responses.analysis_responses import RecommendationResponse
from src.modules.analysis_engine.src.repository_component.repositories.recommendation_repository import (
    RecommendationRepository,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["recommendations"],
)


@router.get(
    "/{recommendation_id}",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recommendation by ID",
    description="Retrieve a specific recommendation. Multi-tenancy is enforced indirectly via analysis.winery_id.",
)
@handle_service_errors
async def get_recommendation(
    recommendation_id: UUID,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repo: Annotated[RecommendationRepository, Depends(get_recommendation_repository)],
) -> RecommendationResponse:
    """
    Retrieve a recommendation by ID.

    Args:
        recommendation_id: UUID of the recommendation
        current_user: Authenticated user context
        repo: Recommendation repository

    Returns:
        RecommendationResponse: The recommendation DTO

    Raises:
        HTTP 401: Not authenticated
        HTTP 404: Recommendation not found
    """
    recommendation = await repo.get_by_id(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )

    return RecommendationResponse.model_validate(recommendation)


@router.put(
    "/{recommendation_id}/apply",
    response_model=RecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a recommendation as applied",
    description=(
        "The winemaker confirms they've applied this recommendation. "
        "Records the timestamp and optional notes. "
        "Requires WINEMAKER or ADMIN role."
    ),
)
@handle_service_errors
async def apply_recommendation(
    recommendation_id: UUID,
    request: RecommendationApplyRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    repo: Annotated[RecommendationRepository, Depends(get_recommendation_repository)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> RecommendationResponse:
    """
    Mark a recommendation as applied by the winemaker.

    This is the confirmation step after the winemaker acts on a recommendation.
    The system tracks applied recommendations to measure effectiveness.

    Args:
        recommendation_id: UUID of the recommendation to apply
        request: Optional application notes
        current_user: Authenticated user context
        repo: Recommendation repository
        session: Database session (for commit after entity mutation)

    Returns:
        RecommendationResponse: Updated recommendation with is_applied=True

    Raises:
        HTTP 401: Not authenticated
        HTTP 403: Insufficient permissions
        HTTP 404: Recommendation not found
        HTTP 409: Recommendation already applied
    """
    recommendation = await repo.get_by_id(recommendation_id)

    if recommendation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {recommendation_id} not found",
        )

    if recommendation.is_applied:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Recommendation {recommendation_id} has already been applied",
        )

    # Apply the recommendation (sets is_applied=True and applied_at=now)
    recommendation.apply()

    # Persist the change
    session.add(recommendation)
    await session.commit()
    await session.refresh(recommendation)

    return RecommendationResponse.model_validate(recommendation)

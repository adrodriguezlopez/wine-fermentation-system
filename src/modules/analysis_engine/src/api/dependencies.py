"""
FastAPI dependencies for Analysis Engine API Layer.

Provides dependency injection for the AnalysisOrchestratorService and
the database session. Following the same pattern as the fermentation module.

Clean Architecture: API layer depends on service abstractions, not implementations.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.fastapi_session import get_db_session
from src.modules.analysis_engine.src.service_component.services.analysis_orchestrator_service import (
    AnalysisOrchestratorService,
)
from src.modules.analysis_engine.src.repository_component.repositories.recommendation_repository import (
    RecommendationRepository,
)


async def get_analysis_orchestrator(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> AnalysisOrchestratorService:
    """
    Dependency: Provide an AnalysisOrchestratorService connected to the current DB session.

    The orchestrator internally creates its sub-services (ComparisonService,
    AnomalyDetectionService, RecommendationService) using the same session.

    Args:
        session: AsyncSession injected by FastAPI from the request lifecycle

    Returns:
        AnalysisOrchestratorService instance ready for use
    """
    return AnalysisOrchestratorService(session)


async def get_recommendation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> RecommendationRepository:
    """
    Dependency: Provide a RecommendationRepository connected to the current DB session.

    Used by the recommendation router for applying individual recommendations
    without running a full analysis.

    Args:
        session: AsyncSession injected by FastAPI from the request lifecycle

    Returns:
        RecommendationRepository instance
    """
    from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager
    session_manager = FastAPISessionManager(session)
    return RecommendationRepository(session_manager)

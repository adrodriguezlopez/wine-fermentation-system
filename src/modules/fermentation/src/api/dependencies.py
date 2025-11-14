"""
FastAPI dependencies for Fermentation API Layer

Provides dependency injection for services, repositories, and real PostgreSQL database.
Following Clean Architecture: API layer depends on service abstractions.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.fastapi_session import get_db_session
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager

from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository
from src.modules.fermentation.src.service_component.interfaces.fermentation_service_interface import IFermentationService
from src.modules.fermentation.src.service_component.services.fermentation_service import FermentationService
from src.modules.fermentation.src.service_component.interfaces.fermentation_validator_interface import IFermentationValidator
from src.modules.fermentation.src.service_component.validators.fermentation_validator import FermentationValidator


def get_fermentation_validator() -> IFermentationValidator:
    """
    Dependency: Get fermentation validator instance
    
    Returns:
        IFermentationValidator: Stateless validator instance
    """
    return FermentationValidator()


async def get_fermentation_repository(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> IFermentationRepository:
    """
    Dependency: Get fermentation repository with real PostgreSQL database session.
    
    Args:
        session: AsyncSession from FastAPI dependency (auto-injected)
    
    Returns:
        IFermentationRepository: Repository instance connected to PostgreSQL
    
    Lifecycle:
        - Session managed by get_db_session (commit/rollback/close automatic)
        - Repository wraps session with SessionManager for BaseRepository compatibility
    """
    session_manager = FastAPISessionManager(session)
    return FermentationRepository(session_manager)


async def get_fermentation_service(
    repository: Annotated[IFermentationRepository, Depends(get_fermentation_repository)],
    validator: Annotated[IFermentationValidator, Depends(get_fermentation_validator)]
) -> IFermentationService:
    """
    Dependency: Get fermentation service instance with injected dependencies.
    
    Args:
        repository: Fermentation repository (auto-injected with PostgreSQL session)
        validator: Fermentation validator (auto-injected)
        
    Returns:
        IFermentationService: Service instance with REAL database persistence
    """
    return FermentationService(
        fermentation_repo=repository,
        validator=validator
    )


"""
Dependency injection for Winery API endpoints.

Provides service instances to route handlers.
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.database.fastapi_session import get_db_session
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager
from src.modules.winery.src.service_component.services.winery_service import WineryService
from src.modules.winery.src.repository_component.repositories.winery_repository import WineryRepository
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import VineyardRepository
from src.modules.fermentation.src.repository_component.repositories.fermentation_repository import FermentationRepository


async def get_winery_service(
    session: Annotated[AsyncSession, Depends(get_db_session)]
) -> WineryService:
    """
    Get WineryService instance with injected repositories.
    
    Requires cross-module repositories for deletion protection:
    - VineyardRepository: Check for active vineyards
    - FermentationRepository: Check for active fermentations
    
    Args:
        session: Database session from dependency injection
        
    Returns:
        Configured WineryService instance
    """
    session_manager = FastAPISessionManager(session)
    winery_repo = WineryRepository(session_manager)
    vineyard_repo = VineyardRepository(session_manager)
    fermentation_repo = FermentationRepository(session_manager)
    
    return WineryService(
        winery_repo=winery_repo,
        vineyard_repo=vineyard_repo,
        fermentation_repo=fermentation_repo
    )

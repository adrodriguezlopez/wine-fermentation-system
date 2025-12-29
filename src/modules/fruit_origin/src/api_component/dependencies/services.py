"""
Dependency Injection for Fruit Origin API

Service layer dependencies for FastAPI endpoints.
"""
from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fruit_origin.src.service_component.interfaces.fruit_origin_service_interface import (
    IFruitOriginService,
)
from src.modules.fruit_origin.src.service_component.services.fruit_origin_service import (
    FruitOriginService,
)
from src.modules.fruit_origin.src.repository_component.repositories.vineyard_repository import (
    VineyardRepository,
)
from src.modules.fruit_origin.src.repository_component.repositories.harvest_lot_repository import (
    HarvestLotRepository,
)
from src.shared.infra.database.fastapi_session import get_db_session
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager


async def get_fruit_origin_service(
    session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[IFruitOriginService, None]:
    """
    Dependency injection for FruitOriginService.
    
    Creates service with all required repositories:
    - VineyardRepository
    - HarvestLotRepository
    
    Args:
        session: Async database session from shared infrastructure
        
    Yields:
        IFruitOriginService: Configured service instance
    """
    session_manager = FastAPISessionManager(session)
    
    vineyard_repo = VineyardRepository(session_manager)
    harvest_lot_repo = HarvestLotRepository(session_manager)
    
    service = FruitOriginService(
        vineyard_repo=vineyard_repo,
        harvest_lot_repo=harvest_lot_repo
    )
    
    yield service

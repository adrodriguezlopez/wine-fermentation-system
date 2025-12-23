"""Winery repository implementation.

Implements ADR-027 Structured Logging:
- LogTimer for database operation timing
- Automatic context binding (winery_id, winery_name)
- Query performance metrics
- Security audit trail for winery data access
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

from src.modules.winery.src.domain.entities.winery import Winery
from src.modules.winery.src.domain.repositories.winery_repository_interface import (
    IWineryRepository,
)
from src.modules.winery.src.domain.dtos.winery_dtos import (
    WineryCreate,
    WineryUpdate,
)
from src.shared.infra.repository.base_repository import BaseRepository

logger = get_logger(__name__)


class RepositoryError(Exception):
    """Base exception for repository errors."""
    pass


class DuplicateNameError(RepositoryError):
    """Raised when attempting to create/update winery with duplicate name."""
    pass


class WineryRepository(BaseRepository, IWineryRepository):
    """
    Implementation of Winery repository.
    
    Handles CRUD operations for Winery entities.
    No multi-tenant scoping (Winery is top-level entity).
    """

    async def create(self, data: WineryCreate) -> Winery:
        """
        Create a new winery.
        
        Args:
            data: Winery creation data
            
        Returns:
            Winery: Created winery entity
            
        Raises:
            DuplicateNameError: If winery with same name exists
            RepositoryError: If creation fails
        """
        async def _create_operation():
            with LogTimer(logger, "create_winery"):
                logger.info(
                    "creating_winery",
                    winery_name=data.name,
                    region=data.region
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    winery = Winery(
                        name=data.name,
                        region=data.region,
                        is_deleted=False,
                    )

                    session.add(winery)
                    await session.flush()
                    await session.refresh(winery)
                    
                    logger.info(
                        "winery_created",
                        winery_id=winery.id,
                        winery_name=winery.name
                    )

                    return winery

        try:
            return await _create_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            # Check for unique constraint on name (works for both PostgreSQL and SQLite)
            if ("uq_wineries__name" in error_str or 
                ("unique constraint" in error_str and "wineries.name" in error_str)):
                logger.warning(
                    "duplicate_winery_name",
                    winery_name=data.name,
                    error_type="DuplicateNameError"
                )
                raise DuplicateNameError(
                    f"Winery with name '{data.name}' already exists"
                ) from e
            raise RepositoryError(f"Failed to create winery: {str(e)}") from e
        except Exception as e:
            logger.error(
                "winery_creation_failed",
                winery_name=data.name,
                error=str(e),
                error_type=type(e).__name__
            )
            raise RepositoryError(f"Failed to create winery: {str(e)}") from e

    async def get_by_id(self, winery_id: int) -> Optional[Winery]:
        """
        Get a winery by ID.
        
        Args:
            winery_id: ID of the winery
            
        Returns:
            Optional[Winery]: Winery entity or None if not found
        """
        async def _get_operation():
            with LogTimer(logger, "get_winery_by_id"):
                logger.debug("fetching_winery", winery_id=winery_id)
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Winery).where(
                        Winery.id == winery_id,
                        Winery.is_deleted == False,
                    )

                    result = await session.execute(query)
                    winery = result.scalar_one_or_none()
                    
                    if winery:
                        logger.debug(
                            "winery_found",
                            winery_id=winery_id,
                            winery_name=winery.name
                        )
                    else:
                        logger.warning("winery_not_found", winery_id=winery_id)
                    
                    return winery

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to get winery: {str(e)}") from e

    async def get_all(self) -> List[Winery]:
        """
        Get all active wineries.
        
        Returns:
            List[Winery]: List of all active winery entities
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(Winery)
                    .where(Winery.is_deleted == False)
                    .order_by(Winery.name.asc())
                )

                result = await session.execute(query)
                return list(result.scalars().all())

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to get all wineries: {str(e)}") from e

    async def get_by_name(self, name: str) -> Optional[Winery]:
        """
        Find a winery by exact name match.
        
        Args:
            name: Exact name of the winery
            
        Returns:
            Optional[Winery]: Winery entity or None if not found
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Winery).where(
                    Winery.name == name,
                    Winery.is_deleted == False,
                )

                result = await session.execute(query)
                return result.scalar_one_or_none()

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to get winery by name: {str(e)}") from e

    async def update(self, winery_id: int, data: WineryUpdate) -> Optional[Winery]:
        """
        Update winery information.
        
        Args:
            winery_id: ID of the winery to update
            data: Winery update data (partial updates supported)
            
        Returns:
            Optional[Winery]: Updated winery entity or None if not found
            
        Raises:
            DuplicateNameError: If updated name conflicts with existing winery
            RepositoryError: If update fails
        """
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Get existing winery
                query = select(Winery).where(
                    Winery.id == winery_id,
                    Winery.is_deleted == False,
                )
                result = await session.execute(query)
                winery = result.scalar_one_or_none()

                if not winery:
                    return None

                # Apply updates
                if data.name is not None:
                    winery.name = data.name
                if data.region is not None:
                    winery.region = data.region

                await session.flush()
                await session.refresh(winery)

                return winery

        try:
            return await _update_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            # Check for unique constraint on name
            if ("uq_wineries__name" in error_str or 
                ("unique constraint" in error_str and "wineries.name" in error_str)):
                raise DuplicateNameError(
                    f"Winery with name '{data.name}' already exists"
                ) from e
            raise RepositoryError(f"Failed to update winery: {str(e)}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to update winery: {str(e)}") from e

    async def delete(self, winery_id: int) -> bool:
        """
        Soft delete a winery (sets is_deleted flag).
        
        Args:
            winery_id: ID of the winery to delete
            
        Returns:
            bool: True if deleted successfully, False if not found
            
        Raises:
            RepositoryError: If deletion fails
        """
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Winery).where(
                    Winery.id == winery_id,
                    Winery.is_deleted == False,
                )
                result = await session.execute(query)
                winery = result.scalar_one_or_none()

                if not winery:
                    return False

                winery.is_deleted = True
                await session.flush()

                return True

        try:
            return await _delete_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to delete winery: {str(e)}") from e

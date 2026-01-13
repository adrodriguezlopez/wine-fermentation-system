"""Vineyard repository implementation.

Implements ADR-027 Structured Logging:
- LogTimer for database operation timing
- Automatic context binding (winery_id, vineyard_id, vineyard_code)
- Query performance metrics
- Security audit trail for vineyard data access
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.repositories.vineyard_repository_interface import (
    IVineyardRepository,
)
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.fruit_origin.src.repository_component.errors import (
    RepositoryError,
    DuplicateCodeError,
)

logger = get_logger(__name__)


class VineyardRepository(BaseRepository, IVineyardRepository):
    """Implementation of Vineyard repository."""

    async def create(self, winery_id: int, data: VineyardCreate) -> Vineyard:
        """Create a new vineyard."""
        async def _create_operation():
            with LogTimer(logger, "create_vineyard"):
                logger.info(
                    "creating_vineyard",
                    winery_id=winery_id,
                    vineyard_code=data.code,
                    vineyard_name=data.name
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    vineyard = Vineyard(
                        winery_id=winery_id,
                        code=data.code,
                        name=data.name,
                        notes=data.notes,
                        is_deleted=False,
                    )

                    session.add(vineyard)
                    await session.flush()
                    await session.refresh(vineyard)
                    
                    logger.info(
                        "vineyard_created",
                        vineyard_id=vineyard.id,
                        winery_id=winery_id,
                        vineyard_code=data.code
                    )

                    return vineyard

        try:
            return await _create_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            # Check for unique constraint on code+winery_id (works for both PostgreSQL and SQLite)
            if ("uq_vineyards__code__winery_id" in error_str or 
                ("unique constraint" in error_str and "vineyards.code" in error_str)):
                logger.warning(
                    "duplicate_vineyard_code",
                    winery_id=winery_id,
                    vineyard_code=data.code,
                    error_type="DuplicateCodeError"
                )
                raise DuplicateCodeError(
                    f"Vineyard with code '{data.code}' already exists for winery {winery_id}"
                ) from e
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e
        except Exception as e:
            logger.error(
                "vineyard_creation_failed",
                winery_id=winery_id,
                vineyard_code=data.code,
                error=str(e),
                error_type=type(e).__name__
            )
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e

    async def get_by_id(self, vineyard_id: int, winery_id: int) -> Optional[Vineyard]:
        """Get a vineyard by ID with winery scoping."""
        async def _get_operation():
            with LogTimer(logger, "get_vineyard_by_id"):
                logger.debug(
                    "fetching_vineyard",
                    vineyard_id=vineyard_id,
                    winery_id=winery_id
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Vineyard).where(
                        Vineyard.id == vineyard_id,
                        Vineyard.winery_id == winery_id,
                        Vineyard.is_deleted == False,
                    )

                    result = await session.execute(query)
                    vineyard = result.scalar_one_or_none()
                    
                    if vineyard:
                        logger.debug(
                            "vineyard_found",
                            vineyard_id=vineyard_id,
                            vineyard_code=vineyard.code
                        )
                    else:
                        logger.warning(
                            "vineyard_not_found",
                            vineyard_id=vineyard_id,
                            winery_id=winery_id
                        )
                    
                    return vineyard

        try:
            return await _get_operation()
        except Exception as e:
            logger.error(
                "vineyard_fetch_failed",
                vineyard_id=vineyard_id,
                winery_id=winery_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise RepositoryError(f"Failed to get vineyard: {str(e)}") from e

    async def get_by_winery(self, winery_id: int) -> List[Vineyard]:
        """Get all vineyards for a winery."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(Vineyard)
                    .where(
                        Vineyard.winery_id == winery_id,
                        Vineyard.is_deleted == False,
                    )
                    .order_by(Vineyard.code.asc())
                )

                result = await session.execute(query)
                return list(result.scalars().all())

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(
                f"Failed to get vineyards for winery {winery_id}: {str(e)}"
            ) from e

    async def get_by_code(self, code: str, winery_id: int) -> Optional[Vineyard]:
        """Get a vineyard by code within a winery."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Vineyard).where(
                    Vineyard.code == code,
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )

                result = await session.execute(query)
                return result.scalar_one_or_none()

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to get vineyard by code: {str(e)}") from e
    
    async def get_by_codes(self, codes: List[str], winery_id: int) -> List[Vineyard]:
        """Get multiple vineyards by codes in a single query (batch loading)."""
        async def _get_operation():
            with LogTimer(logger, "batch_load_vineyards"):
                logger.debug(
                    "batch_loading_vineyards",
                    code_count=len(codes),
                    winery_id=winery_id
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Vineyard).where(
                        Vineyard.code.in_(codes),
                        Vineyard.winery_id == winery_id,
                        Vineyard.is_deleted == False,
                    )

                    result = await session.execute(query)
                    vineyards = result.scalars().all()
                    
                    logger.info(
                        "batch_load_complete",
                        requested_count=len(codes),
                        found_count=len(vineyards),
                        winery_id=winery_id
                    )
                    
                    return vineyards

        try:
            return await _get_operation()
        except Exception as e:
            logger.error(
                "batch_load_failed",
                code_count=len(codes),
                winery_id=winery_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise RepositoryError(f"Failed to batch load vineyards: {str(e)}") from e

    async def update(
        self, vineyard_id: int, winery_id: int, data: VineyardUpdate
    ) -> Optional[Vineyard]:
        """Update a vineyard."""
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Vineyard).where(
                    Vineyard.id == vineyard_id,
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )
                result = await session.execute(query)
                vineyard = result.scalar_one_or_none()
                
                if not vineyard:
                    return None

                # Update only provided fields
                if data.code is not None:
                    vineyard.code = data.code
                if data.name is not None:
                    vineyard.name = data.name
                if data.notes is not None:
                    vineyard.notes = data.notes

                await session.flush()
                await session.refresh(vineyard)

                return vineyard

        try:
            return await _update_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            if ("uq_vineyards__code__winery_id" in error_str or 
                ("unique constraint" in error_str and "vineyards.code" in error_str)):
                raise DuplicateCodeError(
                    f"Vineyard with code '{data.code}' already exists for winery {winery_id}"
                ) from e
            raise RepositoryError(f"Failed to update vineyard: {str(e)}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to update vineyard: {str(e)}") from e

    async def delete(self, vineyard_id: int, winery_id: int) -> bool:
        """Soft delete a vineyard."""
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Vineyard).where(
                    Vineyard.id == vineyard_id,
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )
                result = await session.execute(query)
                vineyard = result.scalar_one_or_none()
                
                if not vineyard:
                    return False

                vineyard.is_deleted = True
                await session.flush()

                return True

        try:
            return await _delete_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to delete vineyard: {str(e)}") from e

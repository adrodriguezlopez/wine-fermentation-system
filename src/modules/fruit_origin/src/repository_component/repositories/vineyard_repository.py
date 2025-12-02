"""Vineyard repository implementation."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

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


class VineyardRepository(BaseRepository, IVineyardRepository):
    """Implementation of Vineyard repository."""

    async def create(self, winery_id: int, data: VineyardCreate) -> Vineyard:
        """Create a new vineyard."""
        async def _create_operation():
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

                return vineyard

        try:
            return await _create_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            # Check for unique constraint on code+winery_id (works for both PostgreSQL and SQLite)
            if ("uq_vineyards__code__winery_id" in error_str or 
                ("unique constraint" in error_str and "vineyards.code" in error_str)):
                raise DuplicateCodeError(
                    f"Vineyard with code '{data.code}' already exists for winery {winery_id}"
                ) from e
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e

    async def get_by_id(self, vineyard_id: int, winery_id: int) -> Optional[Vineyard]:
        """Get a vineyard by ID with winery scoping."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Vineyard).where(
                    Vineyard.id == vineyard_id,
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )

                result = await session.execute(query)
                return result.scalar_one_or_none()

        try:
            return await _get_operation()
        except Exception as e:
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

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

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with async session.

        Args:
            session: SQLAlchemy async session
        """
        super().__init__(session)

    async def create(self, winery_id: int, data: VineyardCreate) -> Vineyard:
        """Create a new vineyard."""
        try:
            vineyard = Vineyard(
                winery_id=winery_id,
                code=data.code,
                name=data.name,
                notes=data.notes,
                is_deleted=False,
            )

            self.session.add(vineyard)
            await self.session.flush()
            await self.session.refresh(vineyard)

            return vineyard

        except IntegrityError as e:
            await self.session.rollback()
            if "uq_vineyards__code__winery_id" in str(e).lower():
                raise DuplicateCodeError(
                    f"Vineyard with code '{data.code}' already exists for winery {winery_id}"
                ) from e
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e

        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to create vineyard: {str(e)}") from e

    async def get_by_id(self, vineyard_id: int, winery_id: int) -> Optional[Vineyard]:
        """Get a vineyard by ID with winery scoping."""
        try:
            query = select(Vineyard).where(
                Vineyard.id == vineyard_id,
                Vineyard.winery_id == winery_id,
                Vineyard.is_deleted == False,
            )

            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            raise RepositoryError(f"Failed to get vineyard: {str(e)}") from e

    async def get_by_winery(self, winery_id: int) -> List[Vineyard]:
        """Get all vineyards for a winery."""
        try:
            query = (
                select(Vineyard)
                .where(
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )
                .order_by(Vineyard.code.asc())
            )

            result = await self.session.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            raise RepositoryError(
                f"Failed to get vineyards for winery {winery_id}: {str(e)}"
            ) from e

    async def get_by_code(self, code: str, winery_id: int) -> Optional[Vineyard]:
        """Get a vineyard by code within a winery."""
        try:
            query = select(Vineyard).where(
                Vineyard.code == code,
                Vineyard.winery_id == winery_id,
                Vineyard.is_deleted == False,
            )

            result = await self.session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            raise RepositoryError(f"Failed to get vineyard by code: {str(e)}") from e

    async def update(
        self, vineyard_id: int, winery_id: int, data: VineyardUpdate
    ) -> Optional[Vineyard]:
        """Update a vineyard."""
        try:
            vineyard = await self.get_by_id(vineyard_id, winery_id)
            if not vineyard:
                return None

            # Update only provided fields
            if data.code is not None:
                vineyard.code = data.code
            if data.name is not None:
                vineyard.name = data.name
            if data.notes is not None:
                vineyard.notes = data.notes

            await self.session.flush()
            await self.session.refresh(vineyard)

            return vineyard

        except IntegrityError as e:
            await self.session.rollback()
            if "uq_vineyards__code__winery_id" in str(e).lower():
                raise DuplicateCodeError(
                    f"Vineyard with code '{data.code}' already exists for winery {winery_id}"
                ) from e
            raise RepositoryError(f"Failed to update vineyard: {str(e)}") from e

        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to update vineyard: {str(e)}") from e

    async def delete(self, vineyard_id: int, winery_id: int) -> bool:
        """Soft delete a vineyard."""
        try:
            vineyard = await self.get_by_id(vineyard_id, winery_id)
            if not vineyard:
                return False

            vineyard.is_deleted = True
            await self.session.flush()

            return True

        except Exception as e:
            await self.session.rollback()
            raise RepositoryError(f"Failed to delete vineyard: {str(e)}") from e

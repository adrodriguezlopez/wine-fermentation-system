"""Vineyard block repository implementation."""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.repositories.vineyard_block_repository_interface import (
    IVineyardBlockRepository,
)
from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import (
    VineyardBlockCreate,
    VineyardBlockUpdate,
)
from src.shared.infra.repository.base_repository import BaseRepository
from src.modules.fruit_origin.src.repository_component.errors import (
    RepositoryError,
    DuplicateCodeError,
    NotFoundError,
)


class VineyardBlockRepository(BaseRepository, IVineyardBlockRepository):
    """Implementation of VineyardBlock repository."""

    async def create(
        self, vineyard_id: int, winery_id: int, data: VineyardBlockCreate
    ) -> VineyardBlock:
        """Create a new vineyard block."""
        async def _create_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Verify vineyard exists and belongs to winery
                vineyard_query = select(Vineyard).where(
                    Vineyard.id == vineyard_id,
                    Vineyard.winery_id == winery_id,
                    Vineyard.is_deleted == False,
                )
                vineyard_result = await session.execute(vineyard_query)
                vineyard = vineyard_result.scalar_one_or_none()

                if not vineyard:
                    raise NotFoundError(
                        f"Vineyard {vineyard_id} not found for winery {winery_id}"
                    )

                block = VineyardBlock(
                    vineyard_id=vineyard_id,
                    code=data.code,
                    soil_type=data.soil_type,
                    slope_pct=data.slope_pct,
                    aspect_deg=data.aspect_deg,
                    area_ha=data.area_ha,
                    elevation_m=data.elevation_m,
                    latitude=data.latitude,
                    longitude=data.longitude,
                    notes=data.notes,
                    irrigation=data.irrigation,
                    organic_certified=data.organic_certified,
                    is_deleted=False,
                )

                session.add(block)
                await session.flush()
                await session.refresh(block)

                return block

        try:
            return await _create_operation()
        except NotFoundError:
            raise
        except IntegrityError as e:
            error_str = str(e).lower()
            if ("uq_vineyard_blocks__code__vineyard_id" in error_str or
                ("unique constraint" in error_str and "vineyard_blocks.code" in error_str)):
                raise DuplicateCodeError(
                    f"Block with code '{data.code}' already exists for vineyard {vineyard_id}"
                ) from e
            raise RepositoryError(f"Failed to create vineyard block: {str(e)}") from e
        except Exception as e:
            raise RepositoryError(f"Failed to create vineyard block: {str(e)}") from e

    async def get_by_id(
        self, block_id: int, winery_id: int
    ) -> Optional[VineyardBlock]:
        """Get a vineyard block by ID with winery scoping."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.id == block_id,
                        Vineyard.winery_id == winery_id,
                        VineyardBlock.is_deleted == False,
                    )
                )

                result = await session.execute(query)
                return result.scalar_one_or_none()

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(f"Failed to get vineyard block: {str(e)}") from e

    async def get_by_vineyard(
        self, vineyard_id: int, winery_id: int
    ) -> List[VineyardBlock]:
        """Get all blocks for a vineyard."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.vineyard_id == vineyard_id,
                        Vineyard.winery_id == winery_id,
                        VineyardBlock.is_deleted == False,
                    )
                    .order_by(VineyardBlock.code.asc())
                )

                result = await session.execute(query)
                return list(result.scalars().all())

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(
                f"Failed to get blocks for vineyard {vineyard_id}: {str(e)}"
            ) from e

    async def get_by_code(
        self, code: str, vineyard_id: int, winery_id: int
    ) -> Optional[VineyardBlock]:
        """Get a vineyard block by code within a vineyard."""
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.code == code,
                        VineyardBlock.vineyard_id == vineyard_id,
                        Vineyard.winery_id == winery_id,
                        VineyardBlock.is_deleted == False,
                    )
                )

                result = await session.execute(query)
                return result.scalar_one_or_none()

        try:
            return await _get_operation()
        except Exception as e:
            raise RepositoryError(
                f"Failed to get vineyard block by code: {str(e)}"
            ) from e

    async def update(
        self, block_id: int, winery_id: int, data: VineyardBlockUpdate
    ) -> Optional[VineyardBlock]:
        """Update a vineyard block."""
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Get block with winery scoping via vineyard join
                query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.id == block_id,
                        Vineyard.winery_id == winery_id,
                        VineyardBlock.is_deleted == False,
                    )
                )
                result = await session.execute(query)
                block = result.scalar_one_or_none()
                if not block:
                    return None

                # Update only provided fields
                if data.code is not None:
                    block.code = data.code
                if data.soil_type is not None:
                    block.soil_type = data.soil_type
                if data.slope_pct is not None:
                    block.slope_pct = data.slope_pct
                if data.aspect_deg is not None:
                    block.aspect_deg = data.aspect_deg
                if data.area_ha is not None:
                    block.area_ha = data.area_ha
                if data.elevation_m is not None:
                    block.elevation_m = data.elevation_m
                if data.latitude is not None:
                    block.latitude = data.latitude
                if data.longitude is not None:
                    block.longitude = data.longitude
                if data.notes is not None:
                    block.notes = data.notes
                if data.irrigation is not None:
                    block.irrigation = data.irrigation
                if data.organic_certified is not None:
                    block.organic_certified = data.organic_certified

                await session.flush()
                await session.refresh(block)

                return block

        try:
            return await _update_operation()
        except IntegrityError as e:
            error_str = str(e).lower()
            if ("uq_vineyard_blocks__code__vineyard_id" in error_str or
                ("unique constraint" in error_str and "vineyard_blocks.code" in error_str)):
                raise DuplicateCodeError(
                    f"Block with code '{data.code}' already exists for vineyard"
                ) from e
            raise RepositoryError(
                f"Failed to update vineyard block: {str(e)}"
            ) from e
        except Exception as e:
            raise RepositoryError(
                f"Failed to update vineyard block: {str(e)}"
            ) from e

    async def delete(self, block_id: int, winery_id: int) -> bool:
        """Soft delete a vineyard block."""
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Get block with winery scoping via vineyard join
                query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.id == block_id,
                        Vineyard.winery_id == winery_id,
                        VineyardBlock.is_deleted == False,
                    )
                )
                result = await session.execute(query)
                block = result.scalar_one_or_none()
                if not block:
                    return False

                block.is_deleted = True
                await session.flush()

                return True

        try:
            return await _delete_operation()
        except Exception as e:
            raise RepositoryError(
                f"Failed to delete vineyard block: {str(e)}"
            ) from e

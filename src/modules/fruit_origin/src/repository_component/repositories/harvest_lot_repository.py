"""
Harvest Lot Repository Implementation.

Concrete implementation of IHarvestLotRepository that extends BaseRepository
and provides database operations for harvest lot management.

Following Domain-Driven Design (ADR-009):
- HarvestLotRepository handles harvest lot CRUD operations
- Real SQLAlchemy queries (not mocked/hardcoded)
- Multi-tenant scoping via winery_id
- Error mapping via BaseRepository
- Returns ORM entities directly (no dataclass mapping needed)
"""

from typing import List, Optional
from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

# Import domain definitions from their canonical locations
from src.modules.fruit_origin.src.domain.repositories.harvest_lot_repository_interface import IHarvestLotRepository
from src.modules.fruit_origin.src.domain.dtos import HarvestLotCreate, HarvestLotUpdate

# Import ORM entities
from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot
from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard

from src.shared.infra.repository.base_repository import BaseRepository


class HarvestLotRepository(BaseRepository, IHarvestLotRepository):
    """
    Repository for harvest lot data operations.

    Implements IHarvestLotRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    
    All methods use real SQLAlchemy queries against the database.
    """

    async def create(self, winery_id: int, data: HarvestLotCreate) -> HarvestLot:
        """
        Creates a new harvest lot record.

        Args:
            winery_id: ID of the winery owning this harvest lot
            data: Harvest lot creation data

        Returns:
            HarvestLot: Created harvest lot entity

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated
            NotFoundError: If block_id does not exist
        """
        async def _create_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Verify block exists and belongs to winery (multi-tenant security)
                block_query = (
                    select(VineyardBlock)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        VineyardBlock.id == data.block_id,
                        Vineyard.winery_id == winery_id
                    )
                )
                result = await session.execute(block_query)
                block = result.scalar_one_or_none()
                
                if not block:
                    from src.modules.fruit_origin.src.repository_component.errors import NotFoundError
                    raise NotFoundError(f"VineyardBlock {data.block_id} not found or access denied")

                # Create ORM entity with provided data
                harvest_lot = HarvestLot(
                    winery_id=winery_id,
                    block_id=data.block_id,
                    code=data.code,
                    harvest_date=data.harvest_date,
                    weight_kg=data.weight_kg,
                    brix_at_harvest=data.brix_at_harvest,
                    brix_method=data.brix_method,
                    brix_measured_at=data.brix_measured_at,
                    grape_variety=data.grape_variety,
                    clone=data.clone,
                    rootstock=data.rootstock,
                    pick_method=data.pick_method,
                    pick_start_time=data.pick_start_time,
                    pick_end_time=data.pick_end_time,
                    bins_count=data.bins_count,
                    field_temp_c=data.field_temp_c,
                    notes=data.notes
                )

                session.add(harvest_lot)
                await session.flush()  # Write to DB to get generated values
                await session.refresh(harvest_lot)  # Load relationships if needed
                
                # Return ORM entity directly (no mapping needed)
                return harvest_lot

        return await self.execute_with_error_mapping(_create_operation)

    async def get_by_id(self, lot_id: int, winery_id: int) -> Optional[HarvestLot]:
        """
        Retrieves a harvest lot by its ID with winery access control.

        Args:
            lot_id: ID of the harvest lot to retrieve
            winery_id: Winery ID for access control

        Returns:
            Optional[HarvestLot]: Harvest lot entity or None if not found
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(HarvestLot).where(
                    HarvestLot.id == lot_id,
                    HarvestLot.winery_id == winery_id,
                    HarvestLot.is_deleted == False
                )

                result = await session.execute(query)
                harvest_lot = result.scalar_one_or_none()

                # Return ORM entity directly (no mapping needed)
                return harvest_lot

        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_winery(self, winery_id: int) -> List[HarvestLot]:
        """
        Retrieves all harvest lots for a specific winery.

        Args:
            winery_id: Winery ID to filter by

        Returns:
            List[HarvestLot]: List of harvest lot entities
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(HarvestLot)
                    .where(
                        HarvestLot.winery_id == winery_id,
                        HarvestLot.is_deleted == False
                    )
                    .order_by(HarvestLot.harvest_date.desc())
                )

                result = await session.execute(query)
                harvest_lots = result.scalars().all()

                # Return list of ORM entities directly (no mapping needed)
                return list(harvest_lots)

        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_code(self, code: str, winery_id: int) -> Optional[HarvestLot]:
        """
        Retrieves a harvest lot by its unique code within a winery.

        Args:
            code: Harvest lot code (unique per winery)
            winery_id: Winery ID for access control

        Returns:
            Optional[HarvestLot]: Harvest lot entity or None if not found
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(HarvestLot).where(
                    HarvestLot.code == code,
                    HarvestLot.winery_id == winery_id,
                    HarvestLot.is_deleted == False
                )

                result = await session.execute(query)
                harvest_lot = result.scalar_one_or_none()

                return harvest_lot

        return await self.execute_with_error_mapping(_get_operation)

    async def get_available_for_blend(
        self, 
        winery_id: int, 
        min_weight_kg: Optional[float] = None
    ) -> List[HarvestLot]:
        """
        Retrieves harvest lots available for blending (not fully used).

        Args:
            winery_id: Winery ID to filter by
            min_weight_kg: Optional minimum weight filter

        Returns:
            List[HarvestLot]: List of available harvest lots
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # For now, return all lots (simplified version)
                # TODO: Add logic to filter out fully used lots by joining with fermentation_lot_sources
                query = (
                    select(HarvestLot)
                    .where(
                        HarvestLot.winery_id == winery_id,
                        HarvestLot.is_deleted == False
                    )
                )

                # Apply min weight filter if provided
                if min_weight_kg is not None:
                    query = query.where(HarvestLot.weight_kg >= min_weight_kg)

                # Order by harvest date (oldest first)
                query = query.order_by(HarvestLot.harvest_date.asc())

                result = await session.execute(query)
                harvest_lots = result.scalars().all()

                return list(harvest_lots)

        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_block(self, block_id: int, winery_id: int) -> List[HarvestLot]:
        """
        Retrieves all harvest lots from a specific vineyard block.

        Args:
            block_id: ID of the vineyard block
            winery_id: Winery ID for access control

        Returns:
            List[HarvestLot]: List of harvest lots from the block
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Multi-tenant security: verify block belongs to winery
                query = (
                    select(HarvestLot)
                    .join(VineyardBlock, HarvestLot.block_id == VineyardBlock.id)
                    .join(Vineyard, VineyardBlock.vineyard_id == Vineyard.id)
                    .where(
                        HarvestLot.block_id == block_id,
                        Vineyard.winery_id == winery_id,
                        HarvestLot.is_deleted == False
                    )
                    .order_by(HarvestLot.harvest_date.desc())
                )

                result = await session.execute(query)
                harvest_lots = result.scalars().all()

                return list(harvest_lots)

        return await self.execute_with_error_mapping(_get_operation)

    async def get_by_harvest_date_range(
        self,
        winery_id: int,
        start_date: date,
        end_date: date
    ) -> List[HarvestLot]:
        """
        Retrieves harvest lots within a date range.

        Args:
            winery_id: Winery ID to filter by
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List[HarvestLot]: List of harvest lots in date range

        Raises:
            ValueError: If start_date > end_date
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = (
                    select(HarvestLot)
                    .where(
                        HarvestLot.winery_id == winery_id,
                        HarvestLot.harvest_date >= start_date,
                        HarvestLot.harvest_date <= end_date,
                        HarvestLot.is_deleted == False
                    )
                    .order_by(HarvestLot.harvest_date.asc())
                )

                result = await session.execute(query)
                harvest_lots = result.scalars().all()

                return list(harvest_lots)

        return await self.execute_with_error_mapping(_get_operation)

    async def update(
        self, 
        lot_id: int, 
        winery_id: int, 
        data: HarvestLotUpdate
    ) -> Optional[HarvestLot]:
        """
        Updates a harvest lot's information.

        Args:
            lot_id: ID of the harvest lot to update
            winery_id: Winery ID for access control
            data: Harvest lot update data (partial updates supported)

        Returns:
            Optional[HarvestLot]: Updated harvest lot entity or None if not found
        """
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Get existing harvest lot
                query = select(HarvestLot).where(
                    HarvestLot.id == lot_id,
                    HarvestLot.winery_id == winery_id,
                    HarvestLot.is_deleted == False
                )

                result = await session.execute(query)
                harvest_lot = result.scalar_one_or_none()

                if not harvest_lot:
                    return None

                # Update fields (only non-None values)
                if data.code is not None:
                    harvest_lot.code = data.code
                if data.harvest_date is not None:
                    harvest_lot.harvest_date = data.harvest_date
                if data.weight_kg is not None:
                    harvest_lot.weight_kg = data.weight_kg
                if data.brix_at_harvest is not None:
                    harvest_lot.brix_at_harvest = data.brix_at_harvest
                if data.brix_method is not None:
                    harvest_lot.brix_method = data.brix_method
                if data.brix_measured_at is not None:
                    harvest_lot.brix_measured_at = data.brix_measured_at
                if data.grape_variety is not None:
                    harvest_lot.grape_variety = data.grape_variety
                if data.clone is not None:
                    harvest_lot.clone = data.clone
                if data.rootstock is not None:
                    harvest_lot.rootstock = data.rootstock
                if data.pick_method is not None:
                    harvest_lot.pick_method = data.pick_method
                if data.pick_start_time is not None:
                    harvest_lot.pick_start_time = data.pick_start_time
                if data.pick_end_time is not None:
                    harvest_lot.pick_end_time = data.pick_end_time
                if data.bins_count is not None:
                    harvest_lot.bins_count = data.bins_count
                if data.field_temp_c is not None:
                    harvest_lot.field_temp_c = data.field_temp_c
                if data.notes is not None:
                    harvest_lot.notes = data.notes

                await session.flush()
                await session.refresh(harvest_lot)

                return harvest_lot

        return await self.execute_with_error_mapping(_update_operation)

    async def delete(self, lot_id: int, winery_id: int) -> bool:
        """
        Soft deletes a harvest lot.

        Args:
            lot_id: ID of the harvest lot to delete
            winery_id: Winery ID for access control

        Returns:
            bool: True if deleted successfully, False if not found
        """
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Get existing harvest lot
                query = select(HarvestLot).where(
                    HarvestLot.id == lot_id,
                    HarvestLot.winery_id == winery_id,
                    HarvestLot.is_deleted == False
                )

                result = await session.execute(query)
                harvest_lot = result.scalar_one_or_none()

                if not harvest_lot:
                    return False

                # Soft delete
                harvest_lot.is_deleted = True
                await session.flush()

                return True

        return await self.execute_with_error_mapping(_delete_operation)

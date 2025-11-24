"""
Lot Source Repository Implementation.

Concrete implementation of ILotSourceRepository that extends BaseRepository
and provides database operations for fermentation lot source management.

Following Domain-Driven Design:
- LotSourceRepository handles lot source CRUD operations
- Real SQLAlchemy queries (not mocked/hardcoded)
- Multi-tenant scoping via fermentation's winery_id
- Error mapping via BaseRepository
- Returns ORM entities directly (no dataclass mapping needed)
"""

from typing import List, Optional
from sqlalchemy import select

# Import domain definitions from their canonical locations
from src.modules.fermentation.src.domain.repositories.lot_source_repository_interface import ILotSourceRepository
from src.modules.fermentation.src.domain.dtos import LotSourceData

# Import ORM entities
from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

from src.shared.infra.repository.base_repository import BaseRepository


class LotSourceRepository(BaseRepository, ILotSourceRepository):
    """
    Repository for fermentation lot source data operations.

    Implements ILotSourceRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    
    All methods use real SQLAlchemy queries against the database.
    """

    async def create(
        self, 
        fermentation_id: int, 
        winery_id: int,
        data: LotSourceData
    ) -> FermentationLotSource:
        """
        Creates a new fermentation lot source record.

        Args:
            fermentation_id: ID of the fermentation using this lot
            winery_id: ID of the winery (for multi-tenant security)
            data: Lot source creation data (harvest_lot_id, mass_used_kg, notes)

        Returns:
            FermentationLotSource: Created lot source entity

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated (e.g., duplicate lot for same fermentation)
            NotFoundError: If fermentation_id or harvest_lot_id does not exist
        """
        async def _create_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Verify fermentation exists and belongs to winery (multi-tenant security)
                fermentation_query = select(Fermentation).where(
                    Fermentation.id == fermentation_id,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False
                )
                result = await session.execute(fermentation_query)
                fermentation = result.scalar_one_or_none()
                
                if not fermentation:
                    from src.shared.domain.exceptions import NotFoundError
                    raise NotFoundError(f"Fermentation {fermentation_id} not found or access denied")

                # Create ORM entity with provided data
                lot_source = FermentationLotSource(
                    fermentation_id=fermentation_id,
                    harvest_lot_id=data.harvest_lot_id,
                    mass_used_kg=float(data.mass_used_kg),  # Convert Decimal to float
                    notes=data.notes
                )

                session.add(lot_source)
                await session.flush()  # Write to DB to get generated values
                await session.refresh(lot_source)  # Load relationships if needed
                
                # Return ORM entity directly (no mapping needed)
                return lot_source

        return await self.execute_with_error_mapping(_create_operation)

    async def get_by_fermentation_id(
        self, 
        fermentation_id: int, 
        winery_id: int
    ) -> List[FermentationLotSource]:
        """
        Retrieves all lot sources for a specific fermentation.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for access control (required for security)

        Returns:
            List[FermentationLotSource]: List of lot source entities (empty if none found)

        Raises:
            RepositoryError: If database operation fails
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Multi-tenant security: JOIN with fermentation to verify winery_id
                query = (
                    select(FermentationLotSource)
                    .join(Fermentation, FermentationLotSource.fermentation_id == Fermentation.id)
                    .where(
                        FermentationLotSource.fermentation_id == fermentation_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )
                )

                result = await session.execute(query)
                lot_sources = result.scalars().all()

                # Return list of ORM entities directly (no mapping needed)
                return list(lot_sources)

        return await self.execute_with_error_mapping(_get_operation)

    async def delete(
        self, 
        lot_source_id: int, 
        winery_id: int
    ) -> bool:
        """
        Deletes a fermentation lot source record.

        Args:
            lot_source_id: ID of the lot source to delete
            winery_id: Winery ID for access control (required for security)

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            RepositoryError: If database operation fails
        """
        async def _delete_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Multi-tenant security: JOIN with fermentation to verify winery_id
                query = (
                    select(FermentationLotSource)
                    .join(Fermentation, FermentationLotSource.fermentation_id == Fermentation.id)
                    .where(
                        FermentationLotSource.id == lot_source_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )
                )

                result = await session.execute(query)
                lot_source = result.scalar_one_or_none()

                if not lot_source:
                    return False

                session.delete(lot_source)  # delete() is synchronous
                await session.flush()
                
                return True

        return await self.execute_with_error_mapping(_delete_operation)

    async def get_by_id(
        self, 
        lot_source_id: int, 
        winery_id: int
    ) -> Optional[FermentationLotSource]:
        """
        Retrieves a specific lot source by its ID.

        Args:
            lot_source_id: ID of the lot source to retrieve
            winery_id: Winery ID for access control (required for security)

        Returns:
            FermentationLotSource | None: Lot source entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Multi-tenant security: JOIN with fermentation to verify winery_id
                query = (
                    select(FermentationLotSource)
                    .join(Fermentation, FermentationLotSource.fermentation_id == Fermentation.id)
                    .where(
                        FermentationLotSource.id == lot_source_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )
                )

                result = await session.execute(query)
                lot_source = result.scalar_one_or_none()

                # Return ORM entity directly (no mapping needed)
                return lot_source

        return await self.execute_with_error_mapping(_get_operation)

    async def update_mass(
        self, 
        lot_source_id: int, 
        winery_id: int,
        new_mass_kg: float
    ) -> Optional[FermentationLotSource]:
        """
        Updates the mass used from a specific lot source.

        Args:
            lot_source_id: ID of the lot source to update
            winery_id: Winery ID for access control (required for security)
            new_mass_kg: New mass in kilograms (must be > 0)

        Returns:
            FermentationLotSource: Updated lot source entity

        Raises:
            RepositoryError: If database operation fails
            NotFoundError: If lot source not found or access denied
            ValueError: If new_mass_kg <= 0
        """
        async def _update_operation():
            if new_mass_kg <= 0:
                raise ValueError("new_mass_kg must be greater than 0")

            session_cm = await self.get_session()
            async with session_cm as session:
                # Multi-tenant security: JOIN with fermentation to verify winery_id
                query = (
                    select(FermentationLotSource)
                    .join(Fermentation, FermentationLotSource.fermentation_id == Fermentation.id)
                    .where(
                        FermentationLotSource.id == lot_source_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )
                )

                result = await session.execute(query)
                lot_source = result.scalar_one_or_none()

                if not lot_source:
                    return None

                # Update mass
                lot_source.mass_used_kg = new_mass_kg
                await session.flush()
                await session.refresh(lot_source)

                # Return updated ORM entity directly (no mapping needed)
                return lot_source

        return await self.execute_with_error_mapping(_update_operation)

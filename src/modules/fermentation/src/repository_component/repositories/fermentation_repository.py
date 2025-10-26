"""
Fermentation Repository Implementation.

Concrete implementation of IFermentationRepository that extends BaseRepository
and provides database operations for fermentation lifecycle management.

Following ADR-003 Separation of Concerns:
- FermentationRepository handles ONLY fermentation lifecycle operations
- Sample operations moved to SampleRepository (see sample_repository.py)
- Real SQLAlchemy queries (not mocked/hardcoded)
- Multi-tenant scoping with winery_id
- Soft delete support
- Error mapping via BaseRepository
- Returns ORM entities directly (no dataclass mapping needed)
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select

# Import domain definitions from their canonical locations
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.dtos import FermentationCreate

# Import ORM entities
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

from src.shared.infra.repository.base_repository import BaseRepository

class FermentationRepository(BaseRepository, IFermentationRepository):
    """
    Repository for fermentation data operations.

    Implements IFermentationRepository using SQLAlchemy ORM with BaseRepository
    infrastructure for session management, error mapping, and multi-tenant security.
    
    All methods use real SQLAlchemy queries against the database.
    """

    async def create(self, winery_id: int, data: FermentationCreate) -> Fermentation:
        """
        Creates a new fermentation record.

        Args:
            winery_id: ID of the winery starting the fermentation
            data: Fermentation creation data

        Returns:
            Fermentation: Created fermentation entity

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated
        """
        async def _create_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Create ORM entity with provided data
                fermentation = Fermentation(
                    winery_id=winery_id,
                    fermented_by_user_id=data.fermented_by_user_id,
                    vintage_year=data.vintage_year,
                    yeast_strain=data.yeast_strain,
                    vessel_code=data.vessel_code,
                    input_mass_kg=data.input_mass_kg,
                    initial_sugar_brix=data.initial_sugar_brix,
                    initial_density=data.initial_density,
                    start_date=data.start_date or datetime.now(),
                    status=FermentationStatus.ACTIVE.value,
                )

                session.add(fermentation)
                await session.flush()  # Write to DB to get generated values
                
                # Return ORM entity directly (no mapping needed)
                # Note: No commit here - BaseRepository/test fixtures handle transaction lifecycle
                return fermentation

        return await self.execute_with_error_mapping(_create_operation)

    async def get_by_id(self, fermentation_id: int, winery_id: int) -> Optional[Fermentation]:
        """
        Retrieves a fermentation by its ID with winery access control.

        Args:
            fermentation_id: ID of the fermentation to retrieve
            winery_id: Winery ID for access control

        Returns:
            Optional[Fermentation]: Fermentation entity or None if not found
        """
        async def _get_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Fermentation).where(
                    Fermentation.id == fermentation_id,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False
                )

                result = await session.execute(query)
                fermentation = result.scalar_one_or_none()

                # Return ORM entity directly (no mapping needed)
                return fermentation

        return await self.execute_with_error_mapping(_get_operation)

    async def update_status(
        self, fermentation_id: int, winery_id: int, new_status: FermentationStatus
    ) -> Optional[Fermentation]:
        """
        Updates the status of a fermentation.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for access control
            new_status: New status value

        Returns:
            Optional[Fermentation]: Updated fermentation or None if not found
        """
        async def _update_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Fermentation).where(
                    Fermentation.id == fermentation_id,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False
                )

                result = await session.execute(query)
                fermentation = result.scalar_one_or_none()

                if fermentation is None:
                    return None

                fermentation.status = new_status.value
                await session.flush()
                await session.refresh(fermentation)
                return fermentation

        return await self.execute_with_error_mapping(_update_operation)

    # ==================================================================================
    # Sample operations REMOVED - Use ISampleRepository (ADR-003)
    # ==================================================================================
    # Sample-related methods have been moved to SampleRepository for proper
    # separation of concerns. FermentationRepository now handles ONLY fermentation
    # lifecycle operations.
    #
    # For sample operations, inject ISampleRepository into your service:
    # - upsert_sample() - Create or update sample
    # - get_latest_sample() - Get most recent sample
    # - get_samples_by_fermentation_id() - Get all samples
    # - get_samples_in_timerange() - Get samples in date range
    # - And 6 more methods...
    #
    # See: src/repository_component/repositories/sample_repository.py (to be implemented)
    # ==================================================================================

    async def get_by_status(
        self, status: FermentationStatus, winery_id: int
    ) -> List[Fermentation]:
        """
        Retrieves fermentations by their current status for a winery.

        Args:
            status: Status to filter by
            winery_id: Winery ID for filtering

        Returns:
            List[Fermentation]: List of fermentations with the specified status
        """
        async def _get_by_status_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                query = select(Fermentation).where(
                    Fermentation.status == status.value,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False
                )

                result = await session.execute(query)
                fermentations = result.scalars().all()

                # Return ORM entities directly
                return list(fermentations)

        return await self.execute_with_error_mapping(_get_by_status_operation)

    async def get_by_winery(
        self, winery_id: int, include_completed: bool = False, include_deleted: bool = False
    ) -> List[Fermentation]:
        """
        Retrieves all fermentations for a winery.

        Args:
            winery_id: ID of the winery
            include_completed: Whether to include completed fermentations
            include_deleted: Whether to include soft-deleted fermentations

        Returns:
            List[Fermentation]: List of fermentations for the winery (ORM entities)
        """
        async def _get_by_winery_operation():
            session_cm = await self.get_session()
            async with session_cm as session:
                # Build query with direct column filtering
                conditions = [Fermentation.winery_id == winery_id]
                
                if not include_deleted:
                    conditions.append(Fermentation.is_deleted == False)
                
                if not include_completed:
                    conditions.append(Fermentation.status != FermentationStatus.COMPLETED.value)
                
                query = select(Fermentation).where(*conditions)
                result = await session.execute(query)
                fermentations = result.scalars().all()
                
                return list(fermentations)

        return await self.execute_with_error_mapping(_get_by_winery_operation)

    async def get_active_by_winery(self, winery_id: int) -> List[Fermentation]:
        """
        Retrieves only active fermentations for a winery.

        Convenience method that filters out completed and deleted fermentations.
        Equivalent to get_by_winery(winery_id, include_completed=False, include_deleted=False)

        Args:
            winery_id: ID of the winery

        Returns:
            List[Fermentation]: List of active fermentations for the winery
        """
        return await self.get_by_winery(
            winery_id=winery_id,
            include_completed=False,
            include_deleted=False
        )

    # NOTE: For comprehensive sample queries, implement ISampleRepository
    # This repository focuses on fermentation lifecycle operations.
    # Sample-specific queries should use SampleRepository:
    # - get_samples_by_fermentation_id() - All samples for a fermentation
    # - get_samples_in_timerange() - Samples within date range
    # - get_latest_sample_by_type() - Latest sample of specific type
    # - check_duplicate_timestamp() - Timestamp validation
    # - bulk_upsert_samples() - Batch operations

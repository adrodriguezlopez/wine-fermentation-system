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

Implements ADR-027 Structured Logging:
- LogTimer for database operation timing
- Automatic context binding (winery_id, fermentation_id)
- Query performance metrics
- Security audit trail (WHO accessed WHAT)
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select

# ADR-027: Structured logging
from src.shared.wine_fermentator_logging import get_logger, LogTimer

# Import domain definitions from their canonical locations
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus
from src.modules.fermentation.src.domain.repositories.fermentation_repository_interface import IFermentationRepository
from src.modules.fermentation.src.domain.dtos import FermentationCreate

# Import ORM entities
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation

from src.shared.infra.repository.base_repository import BaseRepository

logger = get_logger(__name__)


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
            with LogTimer(logger, "create_fermentation"):
                logger.info(
                    "creating_fermentation",
                    winery_id=winery_id,
                    vintage_year=data.vintage_year,
                    vessel_code=data.vessel_code,
                    fermented_by_user_id=data.fermented_by_user_id
                )
                
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
                    
                    logger.info(
                        "fermentation_created",
                        fermentation_id=fermentation.id,
                        winery_id=winery_id,
                        status=fermentation.status
                    )
                    
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
            with LogTimer(logger, "get_fermentation_by_id"):
                logger.debug(
                    "fetching_fermentation",
                    fermentation_id=fermentation_id,
                    winery_id=winery_id
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Fermentation).where(
                        Fermentation.id == fermentation_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )

                    result = await session.execute(query)
                    fermentation = result.scalar_one_or_none()
                    
                    if fermentation:
                        logger.debug(
                            "fermentation_found",
                            fermentation_id=fermentation_id,
                            status=fermentation.status
                        )
                    else:
                        logger.warning(
                            "fermentation_not_found",
                            fermentation_id=fermentation_id,
                            winery_id=winery_id
                        )

                    # Return ORM entity directly (no mapping needed)
                    return fermentation

        return await self.execute_with_error_mapping(_get_operation)

    async def update_status(
        self, 
        fermentation_id: int, 
        winery_id: int, 
        new_status: FermentationStatus,
        metadata: Optional[dict] = None
    ) -> Optional[Fermentation]:
        """
        Updates the status of a fermentation.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for access control
            new_status: New status value
            metadata: Optional metadata about the status change (not currently used)

        Returns:
            Optional[Fermentation]: Updated fermentation or None if not found
        """
        async def _update_operation():
            with LogTimer(logger, "update_fermentation_status"):
                is_soft_delete = metadata and metadata.get('soft_delete', False)
                
                logger.info(
                    "updating_fermentation_status",
                    fermentation_id=fermentation_id,
                    winery_id=winery_id,
                    new_status=new_status.value if not is_soft_delete else "DELETED",
                    is_soft_delete=is_soft_delete
                )
                
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
                        logger.warning(
                            "fermentation_not_found_for_update",
                            fermentation_id=fermentation_id,
                            winery_id=winery_id
                        )
                        return None

                    old_status = fermentation.status
                    
                    # Check if this is a soft delete operation
                    if is_soft_delete:
                        fermentation.is_deleted = True
                        logger.info(
                            "fermentation_soft_deleted",
                            fermentation_id=fermentation_id,
                            winery_id=winery_id,
                            previous_status=old_status
                        )
                    else:
                        fermentation.status = new_status.value
                        logger.info(
                            "fermentation_status_updated",
                            fermentation_id=fermentation_id,
                            winery_id=winery_id,
                            old_status=old_status,
                            new_status=new_status.value
                        )
                    
                    # TODO: Use metadata for full audit trail
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
            with LogTimer(logger, "get_fermentations_by_status"):
                logger.debug(
                    "querying_fermentations_by_status",
                    status=status.value,
                    winery_id=winery_id
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    query = select(Fermentation).where(
                        Fermentation.status == status.value,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False
                    )

                    result = await session.execute(query)
                    fermentations = result.scalars().all()
                    
                    logger.info(
                        "fermentations_retrieved_by_status",
                        status=status.value,
                        winery_id=winery_id,
                        count=len(fermentations)
                    )

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
            with LogTimer(logger, "get_fermentations_by_winery"):
                logger.debug(
                    "querying_fermentations_by_winery",
                    winery_id=winery_id,
                    include_completed=include_completed,
                    include_deleted=include_deleted
                )
                
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
                    
                    logger.info(
                        "fermentations_retrieved_by_winery",
                        winery_id=winery_id,
                        count=len(fermentations),
                        include_completed=include_completed,
                        include_deleted=include_deleted
                    )
                    
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

    async def list_by_data_source(
        self, winery_id: int, data_source: str, include_deleted: bool = False
    ) -> List[Fermentation]:
        """
        Retrieves fermentations filtered by data source (ADR-029).

        Args:
            winery_id: ID of the winery
            data_source: Data source to filter by ('system', 'imported', 'migrated')
            include_deleted: Whether to include soft-deleted fermentations

        Returns:
            List[Fermentation]: List of fermentations with specified data source
        """
        async def _list_by_data_source_operation():
            with LogTimer(logger, "list_fermentations_by_data_source"):
                logger.debug(
                    "querying_fermentations_by_data_source",
                    winery_id=winery_id,
                    data_source=data_source,
                    include_deleted=include_deleted
                )
                
                session_cm = await self.get_session()
                async with session_cm as session:
                    # Build query with data_source filter
                    conditions = [
                        Fermentation.winery_id == winery_id,
                        Fermentation.data_source == data_source
                    ]
                    
                    if not include_deleted:
                        conditions.append(Fermentation.is_deleted == False)
                    
                    query = select(Fermentation).where(*conditions)
                    result = await session.execute(query)
                    fermentations = result.scalars().all()
                    
                    logger.info(
                        "fermentations_retrieved_by_data_source",
                        winery_id=winery_id,
                        data_source=data_source,
                        count=len(fermentations),
                        include_deleted=include_deleted
                    )
                    
                    return list(fermentations)

        return await self.execute_with_error_mapping(_list_by_data_source_operation)

    # NOTE: For comprehensive sample queries, implement ISampleRepository
    # This repository focuses on fermentation lifecycle operations.
    # Sample-specific queries should use SampleRepository:
    # - get_samples_by_fermentation_id() - All samples for a fermentation
    # - get_samples_in_timerange() - Samples within date range
    # - get_latest_sample_by_type() - Latest sample of specific type
    # - check_duplicate_timestamp() - Timestamp validation
    # - bulk_upsert_samples() - Batch operations

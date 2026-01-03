"""
Interface definition for the Fermentation Repository.
Defines the contract that any repository implementation must follow.

Domain-Driven Design Notes:
- This interface lives in the Domain layer and defines business contracts
- Concrete implementations will extend BaseRepository from infrastructure layer
- BaseRepository provides: session management, error mapping, multi-tenant scoping, soft delete
- Uses ORM entities directly as domain entities (no separate dataclasses)
- DTOs are imported from domain.dtos package
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

# Import domain enums from their canonical location
from src.modules.fermentation.src.domain.enums.fermentation_status import FermentationStatus

# Import DTOs from domain.dtos package
from src.modules.fermentation.src.domain.dtos import FermentationCreate

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class IFermentationRepository(ABC):
    """
    Interface for fermentation data persistence.
    Defines core operations for storing and retrieving fermentation data.

    Implementation Notes:
    - Concrete implementations should extend BaseRepository
    - Use BaseRepository helpers: execute_with_error_mapping(), scope_query_by_winery_id(), apply_soft_delete_filter()
    - All operations are multi-tenant aware (winery_id scoping)
    """

    @abstractmethod
    async def create(self, winery_id: int, data: FermentationCreate) -> Fermentation:
        """
        Creates a new fermentation record.

        Args:
            winery_id: ID of the winery starting the fermentation (multi-tenant security)
            data: Fermentation creation data

        Returns:
            Fermentation: Created fermentation entity

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated
        """
        pass

    @abstractmethod
    async def get_by_id(self, fermentation_id: int, winery_id: int) -> Optional[Fermentation]:
        """
        Retrieves a fermentation by its ID with winery access control.

        Args:
            fermentation_id: ID of the fermentation to retrieve
            winery_id: Winery ID for access control (required for security)

        Returns:
            Optional[Fermentation]: Fermentation entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
    async def update_status(
        self,
        fermentation_id: int,
        winery_id: int,
        new_status: FermentationStatus,
        metadata: Optional[dict[str, any]] = None,
    ) -> bool:
        """
        Updates the status of a fermentation with optimistic locking.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: Winery ID for access control
            new_status: New status value
            metadata: Optional metadata about the status change

        Returns:
            bool: True if update was successful

        Raises:
            NotFoundError: If fermentation_id doesn't exist or winery_id doesn't match
            ValidationError: If new_status is invalid
            ConcurrentModificationError: If fermentation was modified by another process
        """
        pass

    # ==================================================================================
    # NOTE: Sample operations have been moved to ISampleRepository
    # ==================================================================================
    # For ALL sample-related operations, use ISampleRepository directly:
    # - upsert_sample() - Create or update sample
    # - get_sample_by_id() - Get individual sample
    # - get_samples_by_fermentation_id() - All samples for a fermentation
    # - get_samples_in_timerange() - Samples within date range
    # - get_latest_sample() - Most recent sample
    # - get_latest_sample_by_type() - Latest sample of specific type
    # - check_duplicate_timestamp() - Timestamp validation
    # - soft_delete_sample() - Soft delete sample
    # - bulk_upsert_samples() - Batch operations
    #
    # See: src/domain/repositories/sample_repository_interface.py
    #
    # Rationale: Separation of Concerns (ADR-003)
    # - FermentationRepository handles ONLY fermentation lifecycle
    # - SampleRepository handles ALL sample operations
    # ==================================================================================

    @abstractmethod
    async def get_by_status(
        self, status: FermentationStatus, winery_id: int
    ) -> List[Fermentation]:
        """
        Retrieves fermentations by their current status for a winery.

        Args:
            status: Status to filter by
            winery_id: Winery ID for filtering (required for security)

        Returns:
            List[Fermentation]: List of fermentations with the specified status

        Raises:
            ValidationError: If status is invalid
        """
        pass

    @abstractmethod
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
            List[Fermentation]: List of fermentations for the winery

        Raises:
            RepositoryError: If database operation fails
        """
        pass

    @abstractmethod
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

        Raises:
            RepositoryError: If database operation fails
        """
        pass
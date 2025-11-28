"""
Interface definition for the HarvestLot Repository.
Defines the contract that any harvest lot repository implementation must follow.

Domain-Driven Design Notes:
- This interface lives in the Domain layer and defines business contracts
- Concrete implementations will extend BaseRepository from infrastructure layer
- BaseRepository provides: session management, error mapping, multi-tenant scoping, soft delete
- Uses ORM entities directly as domain entities (no separate dataclasses)
- DTOs are imported from domain.dtos package

Related ADRs:
- ADR-001: Fruit Origin Model (defines HarvestLot entity)
- ADR-002: Repository Architecture (defines repository pattern)
- ADR-009: Missing Repositories Implementation (this repository)
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from datetime import date

if TYPE_CHECKING:
    from src.modules.fruit_origin.src.domain.entities.harvest_lot import HarvestLot


class IHarvestLotRepository(ABC):
    """
    Interface for harvest lot data persistence.
    Defines core operations for storing and retrieving harvest lot data.

    Implementation Notes:
    - Concrete implementations should extend BaseRepository
    - Use BaseRepository helpers: execute_with_error_mapping(), scope_query_by_winery_id(), apply_soft_delete_filter()
    - All operations are multi-tenant aware (winery_id scoping)
    
    Business Rules:
    - HarvestLot.code must be unique per winery (unique constraint)
    - All operations must validate winery_id for multi-tenant security
    - Soft delete supported (is_deleted flag)
    """

    @abstractmethod
    async def create(self, winery_id: int, data: 'HarvestLotCreate') -> HarvestLot:
        """
        Creates a new harvest lot record.

        Args:
            winery_id: ID of the winery owning this harvest lot (multi-tenant security)
            data: Harvest lot creation data

        Returns:
            HarvestLot: Created harvest lot entity

        Raises:
            RepositoryError: If creation fails
            IntegrityError: If constraints are violated (e.g., duplicate code per winery)
            NotFoundError: If block_id does not exist
        
        Business Rules Enforced:
            - Harvest lot code must be unique per winery
            - Vineyard block must exist and belong to same winery
            - Weight must be positive
        """
        pass

    @abstractmethod
    async def get_by_id(self, lot_id: int, winery_id: int) -> Optional[HarvestLot]:
        """
        Retrieves a harvest lot by its ID with winery access control.

        Args:
            lot_id: ID of the harvest lot to retrieve
            winery_id: Winery ID for access control (required for security)

        Returns:
            Optional[HarvestLot]: Harvest lot entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        
        Use Cases:
            - Display harvest lot details
            - Validate lot exists before creating blend
            - Update harvest lot information
        """
        pass

    @abstractmethod
    async def get_by_winery(self, winery_id: int) -> List[HarvestLot]:
        """
        Retrieves all harvest lots for a specific winery.

        Args:
            winery_id: Winery ID to filter by

        Returns:
            List[HarvestLot]: List of harvest lot entities (empty if none found)

        Raises:
            RepositoryError: If database operation fails
        
        Use Cases:
            - List all harvest lots in admin interface
            - Generate harvest reports
            - Export harvest data
        """
        pass

    @abstractmethod
    async def get_by_code(self, code: str, winery_id: int) -> Optional[HarvestLot]:
        """
        Retrieves a harvest lot by its unique code within a winery.

        Args:
            code: Harvest lot code (unique per winery)
            winery_id: Winery ID for access control

        Returns:
            Optional[HarvestLot]: Harvest lot entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        
        Use Cases:
            - Validate code uniqueness before creation
            - Lookup by barcode/QR code
            - Import validation
        """
        pass

    @abstractmethod
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

        Raises:
            RepositoryError: If database operation fails
        
        Business Logic:
            - Filters out lots that are fully used in fermentations
            - Optionally filters by minimum weight
            - Orders by harvest_date (oldest first)
        
        Use Cases:
            - CRITICAL: Blend creation feature (ADR-001)
            - Select lots for new fermentation
            - Inventory management
        """
        pass

    @abstractmethod
    async def get_by_block(self, block_id: int, winery_id: int) -> List[HarvestLot]:
        """
        Retrieves all harvest lots from a specific vineyard block.

        Args:
            block_id: ID of the vineyard block
            winery_id: Winery ID for access control

        Returns:
            List[HarvestLot]: List of harvest lots from the block

        Raises:
            RepositoryError: If database operation fails
        
        Use Cases:
            - View harvest history by block
            - Vineyard block performance analysis
            - Traceability queries
        """
        pass

    @abstractmethod
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
            RepositoryError: If database operation fails
            ValueError: If start_date > end_date
        
        Use Cases:
            - Vintage reports
            - Seasonal analysis
            - Historical comparisons
        """
        pass

    @abstractmethod
    async def update(
        self, 
        lot_id: int, 
        winery_id: int, 
        data: 'HarvestLotUpdate'
    ) -> Optional[HarvestLot]:
        """
        Updates a harvest lot's information.

        Args:
            lot_id: ID of the harvest lot to update
            winery_id: Winery ID for access control
            data: Harvest lot update data (partial updates supported)

        Returns:
            Optional[HarvestLot]: Updated harvest lot entity or None if not found

        Raises:
            RepositoryError: If database operation fails
            NotFoundError: If lot_id not found or access denied
            IntegrityError: If constraints violated (e.g., duplicate code)
        
        Use Cases:
            - Correct harvest data entry errors
            - Update brix measurements
            - Add notes or metadata
        """
        pass

    @abstractmethod
    async def delete(self, lot_id: int, winery_id: int) -> bool:
        """
        Soft deletes a harvest lot.

        Args:
            lot_id: ID of the harvest lot to delete
            winery_id: Winery ID for access control

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            RepositoryError: If database operation fails
            IntegrityError: If lot is referenced by fermentations (FK constraint)
        
        Note:
            - Soft delete sets is_deleted=True
            - Cannot delete if lot is used in any fermentation (FK constraint)
            - Consider archiving instead of deleting
        """
        pass

"""
Interface definition for the Fermentation Lot Source Repository.
Defines the contract that any lot source repository implementation must follow.

Domain-Driven Design Notes:
- This interface lives in the Domain layer and defines business contracts
- Concrete implementations will extend BaseRepository from infrastructure layer
- BaseRepository provides: session management, error mapping, multi-tenant scoping, soft delete
- Uses ORM entities directly as domain entities (no separate dataclasses)
- DTOs are imported from domain.dtos package
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, TYPE_CHECKING

# Import DTOs from domain.dtos package
from src.modules.fermentation.src.domain.dtos import LotSourceData

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource


class ILotSourceRepository(ABC):
    """
    Interface for fermentation lot source data persistence.
    Defines core operations for storing and retrieving lot source associations.

    Implementation Notes:
    - Concrete implementations should extend BaseRepository
    - Use BaseRepository helpers: execute_with_error_mapping(), scope_query_by_winery_id()
    - All operations are multi-tenant aware (winery_id scoping via fermentation)
    - Lot sources are tightly coupled to fermentations (cascade delete)
    """

    @abstractmethod
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
        
        Business Rules Enforced:
            - Fermentation and harvest lot must belong to same winery
            - No duplicate harvest lot per fermentation (unique constraint)
            - mass_used_kg must be positive (check constraint)
        """
        pass

    @abstractmethod
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
        
        Use Cases:
            - Display blend composition in fermentation detail view
            - Validate mass consistency (sum of masses = fermentation input mass)
            - Traceability queries (fruit origin)
        """
        pass

    @abstractmethod
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
        
        Use Cases:
            - Modify blend composition before fermentation starts
            - Correct data entry errors
            - Cascade delete handled by ORM when fermentation is deleted
        """
        pass

    @abstractmethod
    async def get_by_id(
        self, 
        lot_source_id: int, 
        winery_id: int
    ) -> FermentationLotSource | None:
        """
        Retrieves a specific lot source by its ID.

        Args:
            lot_source_id: ID of the lot source to retrieve
            winery_id: Winery ID for access control (required for security)

        Returns:
            FermentationLotSource | None: Lot source entity or None if not found

        Raises:
            RepositoryError: If database operation fails
        
        Use Cases:
            - Update operations (fetch before modify)
            - Detail views for specific lot source
        """
        pass

    @abstractmethod
    async def update_mass(
        self, 
        lot_source_id: int, 
        winery_id: int,
        new_mass_kg: float
    ) -> FermentationLotSource:
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
        
        Use Cases:
            - Adjust blend proportions during fermentation setup
            - Correct measurement errors
        """
        pass

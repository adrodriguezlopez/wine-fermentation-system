"""Vineyard repository interface for fruit origin module."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.fruit_origin.src.domain.entities.vineyard import Vineyard
from src.modules.fruit_origin.src.domain.dtos.vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)


class IVineyardRepository(ABC):
    """Interface for Vineyard repository operations."""

    @abstractmethod
    async def create(self, winery_id: int, data: VineyardCreate) -> Vineyard:
        """
        Create a new vineyard.

        Args:
            winery_id: ID of the winery owning the vineyard
            data: Vineyard creation data

        Returns:
            Created Vineyard entity

        Raises:
            RepositoryError: If creation fails
            DuplicateCodeError: If code already exists for this winery
        """
        pass

    @abstractmethod
    async def get_by_id(self, vineyard_id: int, winery_id: int) -> Optional[Vineyard]:
        """
        Get a vineyard by ID with winery scoping.

        Args:
            vineyard_id: ID of the vineyard
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            Vineyard entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_winery(self, winery_id: int) -> List[Vineyard]:
        """
        Get all vineyards for a winery.

        Args:
            winery_id: ID of the winery

        Returns:
            List of Vineyard entities (empty if none found)
        """
        pass

    @abstractmethod
    async def get_by_code(self, code: str, winery_id: int) -> Optional[Vineyard]:
        """
        Get a vineyard by code within a winery.

        Args:
            code: Vineyard code
            winery_id: ID of the winery

        Returns:
            Vineyard entity if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def get_by_codes(self, codes: List[str], winery_id: int) -> List[Vineyard]:
        """
        Get multiple vineyards by codes in a single query (batch loading).
        
        This eliminates N+1 query problems when loading vineyards for multiple fermentations.
        
        Args:
            codes: List of vineyard codes to load
            winery_id: ID of the winery (for multi-tenant security)
            
        Returns:
            List of Vineyard entities (may be fewer than codes if some don't exist)
            
        Example:
            # Instead of 1000 queries:
            # for code in codes:
            #     vineyard = await get_by_code(code, winery_id)
            #
            # Use batch loading (1 query):
            # vineyards = await get_by_codes(codes, winery_id)
        """
        pass

    @abstractmethod
    async def update(
        self, vineyard_id: int, winery_id: int, data: VineyardUpdate
    ) -> Optional[Vineyard]:
        """
        Update a vineyard.

        Args:
            vineyard_id: ID of the vineyard to update
            winery_id: ID of the winery (for multi-tenant security)
            data: Update data

        Returns:
            Updated Vineyard entity if found, None otherwise

        Raises:
            RepositoryError: If update fails
            DuplicateCodeError: If code already exists for this winery
        """
        pass

    @abstractmethod
    async def delete(self, vineyard_id: int, winery_id: int) -> bool:
        """
        Soft delete a vineyard.

        Args:
            vineyard_id: ID of the vineyard to delete
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

"""Vineyard block repository interface for fruit origin module."""
from abc import ABC, abstractmethod
from typing import List, Optional

from src.modules.fruit_origin.src.domain.entities.vineyard_block import VineyardBlock
from src.modules.fruit_origin.src.domain.dtos.vineyard_block_dtos import (
    VineyardBlockCreate,
    VineyardBlockUpdate,
)


class IVineyardBlockRepository(ABC):
    """Interface for VineyardBlock repository operations."""

    @abstractmethod
    async def create(
        self, vineyard_id: int, winery_id: int, data: VineyardBlockCreate
    ) -> VineyardBlock:
        """
        Create a new vineyard block.

        Args:
            vineyard_id: ID of the vineyard
            winery_id: ID of the winery (for multi-tenant security)
            data: Block creation data

        Returns:
            Created VineyardBlock entity

        Raises:
            RepositoryError: If creation fails
            DuplicateCodeError: If code already exists for this vineyard
            NotFoundError: If vineyard not found or doesn't belong to winery
        """
        pass

    @abstractmethod
    async def get_by_id(self, block_id: int, winery_id: int) -> Optional[VineyardBlock]:
        """
        Get a vineyard block by ID with winery scoping.

        Args:
            block_id: ID of the block
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            VineyardBlock entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_by_vineyard(
        self, vineyard_id: int, winery_id: int
    ) -> List[VineyardBlock]:
        """
        Get all blocks for a vineyard.

        Args:
            vineyard_id: ID of the vineyard
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            List of VineyardBlock entities (empty if none found)
        """
        pass

    @abstractmethod
    async def get_by_code(
        self, code: str, vineyard_id: int, winery_id: int
    ) -> Optional[VineyardBlock]:
        """
        Get a vineyard block by code within a vineyard.

        Args:
            code: Block code
            vineyard_id: ID of the vineyard
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            VineyardBlock entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def update(
        self, block_id: int, winery_id: int, data: VineyardBlockUpdate
    ) -> Optional[VineyardBlock]:
        """
        Update a vineyard block.

        Args:
            block_id: ID of the block to update
            winery_id: ID of the winery (for multi-tenant security)
            data: Update data

        Returns:
            Updated VineyardBlock entity if found, None otherwise

        Raises:
            RepositoryError: If update fails
            DuplicateCodeError: If code already exists for this vineyard
        """
        pass

    @abstractmethod
    async def delete(self, block_id: int, winery_id: int) -> bool:
        """
        Soft delete a vineyard block.

        Args:
            block_id: ID of the block to delete
            winery_id: ID of the winery (for multi-tenant security)

        Returns:
            True if deleted, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

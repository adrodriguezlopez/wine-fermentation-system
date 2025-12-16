"""
Winery Repository Interface.

Defines the contract for winery data operations following Domain-Driven Design.
Winery is a top-level entity (no winery_id scoping needed).

Following ADR-009: Phase 3 - Winery Repository Implementation
"""

from abc import ABC, abstractmethod
from typing import List, Optional

# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.modules.winery.src.domain.entities.winery import Winery
    from src.modules.winery.src.domain.dtos.winery_dtos import WineryCreate, WineryUpdate


class IWineryRepository(ABC):
    """
    Interface for winery repository operations.
    
    Winery is a top-level entity with no multi-tenant scoping.
    All operations are admin-level (authorization handled at service/API layer).
    
    Methods:
        create: Create a new winery
        get_by_id: Retrieve winery by ID
        get_all: Retrieve all wineries
        get_by_name: Find winery by exact name match
        update: Update winery information
        delete: Soft delete a winery (sets is_deleted flag)
    """

    @abstractmethod
    async def create(self, data: "WineryCreate") -> "Winery":
        """
        Create a new winery.

        Args:
            data: Winery creation data

        Returns:
            Winery: Created winery entity

        Raises:
            DuplicateNameError: If winery with same name already exists
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(self, winery_id: int) -> Optional["Winery"]:
        """
        Retrieve a winery by its ID.

        Args:
            winery_id: ID of the winery to retrieve

        Returns:
            Optional[Winery]: Winery entity or None if not found
        """
        pass

    @abstractmethod
    async def get_all(self) -> List["Winery"]:
        """
        Retrieve all active wineries (not soft-deleted).

        Returns:
            List[Winery]: List of all active winery entities
        """
        pass

    @abstractmethod
    async def get_by_name(self, name: str) -> Optional["Winery"]:
        """
        Find a winery by exact name match.

        Args:
            name: Exact name of the winery

        Returns:
            Optional[Winery]: Winery entity or None if not found
        """
        pass

    @abstractmethod
    async def update(self, winery_id: int, data: "WineryUpdate") -> Optional["Winery"]:
        """
        Update winery information.

        Args:
            winery_id: ID of the winery to update
            data: Winery update data (partial updates supported)

        Returns:
            Optional[Winery]: Updated winery entity or None if not found

        Raises:
            DuplicateNameError: If updated name conflicts with existing winery
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(self, winery_id: int) -> bool:
        """
        Soft delete a winery (sets is_deleted flag).

        Args:
            winery_id: ID of the winery to delete

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

"""
Fermentation Note Repository Interface.

Defines the contract for fermentation note data operations following Domain-Driven Design.
Multi-tenant security enforced via JOIN with fermentation table.

Following ADR-009: Phase 3 - Fermentation Note Repository Implementation
"""

from abc import ABC, abstractmethod
from typing import List, Optional

# Forward references for type hints
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
    from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
        FermentationNoteCreate,
        FermentationNoteUpdate,
    )


class IFermentationNoteRepository(ABC):
    """
    Interface for fermentation note repository operations.
    
    Security: Multi-tenant via JOIN with fermentation table.
    All operations validate that the fermentation belongs to the winery.
    
    Methods:
        create: Create a new fermentation note
        get_by_id: Retrieve note by ID with winery scoping
        get_by_fermentation: Retrieve all notes for a fermentation
        update: Update note information
        delete: Soft delete a note
    """

    @abstractmethod
    async def create(
        self, 
        fermentation_id: int,
        winery_id: int,
        data: "FermentationNoteCreate"
    ) -> "FermentationNote":
        """
        Create a new fermentation note.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: ID of the winery (for security)
            data: Note creation data

        Returns:
            FermentationNote: Created note entity

        Raises:
            NotFoundError: If fermentation doesn't exist or doesn't belong to winery
            RepositoryError: If creation fails
        """
        pass

    @abstractmethod
    async def get_by_id(
        self, 
        note_id: int, 
        winery_id: int
    ) -> Optional["FermentationNote"]:
        """
        Retrieve a fermentation note by its ID.
        
        Security: Validates note's fermentation belongs to winery via JOIN.

        Args:
            note_id: ID of the note to retrieve
            winery_id: ID of the winery (for security)

        Returns:
            Optional[FermentationNote]: Note entity or None if not found
        """
        pass

    @abstractmethod
    async def get_by_fermentation(
        self, 
        fermentation_id: int, 
        winery_id: int
    ) -> List["FermentationNote"]:
        """
        Retrieve all notes for a fermentation.
        
        Security: Validates fermentation belongs to winery.

        Args:
            fermentation_id: ID of the fermentation
            winery_id: ID of the winery (for security)

        Returns:
            List[FermentationNote]: List of note entities (ordered by created_at DESC)
        """
        pass

    @abstractmethod
    async def update(
        self, 
        note_id: int, 
        winery_id: int,
        data: "FermentationNoteUpdate"
    ) -> Optional["FermentationNote"]:
        """
        Update fermentation note information.
        
        Security: Validates note's fermentation belongs to winery.

        Args:
            note_id: ID of the note to update
            winery_id: ID of the winery (for security)
            data: Note update data (partial updates supported)

        Returns:
            Optional[FermentationNote]: Updated note entity or None if not found

        Raises:
            RepositoryError: If update fails
        """
        pass

    @abstractmethod
    async def delete(
        self, 
        note_id: int, 
        winery_id: int
    ) -> bool:
        """
        Soft delete a fermentation note (sets is_deleted flag).
        
        Security: Validates note's fermentation belongs to winery.

        Args:
            note_id: ID of the note to delete
            winery_id: ID of the winery (for security)

        Returns:
            bool: True if deleted successfully, False if not found

        Raises:
            RepositoryError: If deletion fails
        """
        pass

"""
FermentationNoteService — service layer for FermentationNote.

Responsibilities:
  - add_note: validate and create a note for a fermentation
  - get_note: retrieve a note by ID with winery scoping
  - get_notes_for_fermentation: list all notes for a fermentation
  - update_note: partial update of note content
  - delete_note: soft delete a note
"""

from typing import List, Optional

from src.modules.fermentation.src.domain.entities.fermentation_note import (
    FermentationNote,
)
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError
from src.shared.wine_fermentator_logging import get_logger

logger = get_logger(__name__)


class FermentationNoteNotFoundError(Exception):
    """Raised when a fermentation note cannot be found or does not belong to the winery."""


class FermentationNoteService:
    """
    Service layer for FermentationNote management.

    Depends on IFermentationNoteRepository for data access.
    Multi-tenant security enforced via winery_id scoping in the repository.
    """

    def __init__(self, note_repo: IFermentationNoteRepository) -> None:
        self._repo = note_repo

    # ------------------------------------------------------------------
    # Command: add a note
    # ------------------------------------------------------------------

    async def add_note(
        self,
        fermentation_id: int,
        winery_id: int,
        note_text: str,
        action_taken: str,
        created_by_user_id: int,
    ) -> FermentationNote:
        """
        Add a free-text note to a fermentation.

        Args:
            fermentation_id: ID of the fermentation to annotate.
            winery_id: Winery context for multi-tenant validation.
            note_text: Free-text observation from the winemaker.
            action_taken: Short description of the action taken.
            created_by_user_id: ID of the winemaker writing the note.

        Returns:
            The created FermentationNote entity.

        Raises:
            EntityNotFoundError: If the fermentation does not exist or does not
                belong to the winery.
        """
        dto = FermentationNoteCreate(
            note_text=note_text,
            action_taken=action_taken,
            created_by_user_id=created_by_user_id,
        )
        note = await self._repo.create(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            data=dto,
        )
        logger.info(
            "fermentation_note_added",
            note_id=note.id,
            fermentation_id=fermentation_id,
            winery_id=winery_id,
        )
        return note

    # ------------------------------------------------------------------
    # Query: get a single note
    # ------------------------------------------------------------------

    async def get_note(self, note_id: int, winery_id: int) -> FermentationNote:
        """
        Retrieve a single note by ID.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or
                does not belong to the winery.
        """
        note = await self._repo.get_by_id(note_id=note_id, winery_id=winery_id)
        if note is None:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found for winery {winery_id}"
            )
        return note

    # ------------------------------------------------------------------
    # Query: list notes for a fermentation
    # ------------------------------------------------------------------

    async def get_notes_for_fermentation(
        self, fermentation_id: int, winery_id: int
    ) -> List[FermentationNote]:
        """
        Return all notes for a fermentation, ordered newest-first.

        Returns an empty list if the fermentation has no notes or does not
        belong to the winery.
        """
        return await self._repo.get_by_fermentation(
            fermentation_id=fermentation_id, winery_id=winery_id
        )

    # ------------------------------------------------------------------
    # Command: update a note
    # ------------------------------------------------------------------

    async def update_note(
        self,
        note_id: int,
        winery_id: int,
        note_text: Optional[str] = None,
        action_taken: Optional[str] = None,
    ) -> FermentationNote:
        """
        Partially update a note's content.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or does
                not belong to the winery.
        """
        dto = FermentationNoteUpdate(
            note_text=note_text,
            action_taken=action_taken,
        )
        note = await self._repo.update(note_id=note_id, winery_id=winery_id, data=dto)
        if note is None:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found for winery {winery_id}"
            )
        logger.info("fermentation_note_updated", note_id=note_id, winery_id=winery_id)
        return note

    # ------------------------------------------------------------------
    # Command: delete a note
    # ------------------------------------------------------------------

    async def delete_note(self, note_id: int, winery_id: int) -> None:
        """
        Soft-delete a note.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or does
                not belong to the winery.
        """
        deleted = await self._repo.delete(note_id=note_id, winery_id=winery_id)
        if not deleted:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found for winery {winery_id}"
            )
        logger.info("fermentation_note_deleted", note_id=note_id, winery_id=winery_id)

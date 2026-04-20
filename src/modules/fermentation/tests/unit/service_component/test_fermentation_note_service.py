"""
Unit tests for FermentationNoteService.

All tests use MagicMock / AsyncMock to avoid any database dependency.
TDD: Tests written before the service implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.modules.fermentation.src.domain.entities.fermentation_note import (
    FermentationNote,
)
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
    FermentationNoteService,
    FermentationNoteNotFoundError,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_note(**kwargs) -> FermentationNote:
    """Build a FermentationNote mock with sensible defaults."""
    defaults = dict(
        id=1,
        fermentation_id=10,
        note_text="Initial fermentation looks good",
        action_taken="Checked temperature",
        created_by_user_id=5,
        winery_id=100,
        is_deleted=False,
        created_at=datetime(2026, 4, 1, 10, 0, 0),
        updated_at=datetime(2026, 4, 1, 10, 0, 0),
    )
    defaults.update(kwargs)
    note = MagicMock(spec=FermentationNote)
    for k, v in defaults.items():
        setattr(note, k, v)
    return note


def _make_service() -> tuple:
    """Return (service, repo_mock)."""
    repo_mock = AsyncMock()
    service = FermentationNoteService(note_repo=repo_mock)
    return service, repo_mock


# =============================================================================
# add_note
# =============================================================================


class TestAddNote:

    @pytest.mark.asyncio
    async def test_creates_note_with_correct_fields(self):
        service, repo = _make_service()
        expected = _make_note()
        repo.create.return_value = expected

        result = await service.add_note(
            fermentation_id=10,
            winery_id=100,
            note_text="Initial fermentation looks good",
            action_taken="Checked temperature",
            created_by_user_id=5,
        )

        assert result == expected
        repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_dto_passed_correctly(self):
        service, repo = _make_service()
        repo.create.return_value = _make_note()

        await service.add_note(
            fermentation_id=10,
            winery_id=100,
            note_text="Glucose drop observed",
            action_taken="No action",
            created_by_user_id=5,
        )

        call_args = repo.create.call_args
        assert call_args.kwargs["fermentation_id"] == 10
        assert call_args.kwargs["winery_id"] == 100
        dto = call_args.kwargs["data"]
        assert dto.note_text == "Glucose drop observed"
        assert dto.action_taken == "No action"
        assert dto.created_by_user_id == 5

    @pytest.mark.asyncio
    async def test_propagates_repo_error(self):
        service, repo = _make_service()
        from src.modules.fermentation.src.repository_component.errors import (
            EntityNotFoundError,
        )

        repo.create.side_effect = EntityNotFoundError("Fermentation not found")

        with pytest.raises(EntityNotFoundError):
            await service.add_note(
                fermentation_id=999,
                winery_id=100,
                note_text="note",
                action_taken="action",
                created_by_user_id=5,
            )


# =============================================================================
# get_note
# =============================================================================


class TestGetNote:

    @pytest.mark.asyncio
    async def test_returns_note_when_found(self):
        service, repo = _make_service()
        expected = _make_note(id=1)
        repo.get_by_id.return_value = expected

        result = await service.get_note(note_id=1, winery_id=100)

        assert result == expected
        repo.get_by_id.assert_called_once_with(note_id=1, winery_id=100)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_note_missing(self):
        service, repo = _make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(FermentationNoteNotFoundError):
            await service.get_note(note_id=999, winery_id=100)

    @pytest.mark.asyncio
    async def test_raises_not_found_with_correct_message(self):
        service, repo = _make_service()
        repo.get_by_id.return_value = None

        with pytest.raises(FermentationNoteNotFoundError, match="999"):
            await service.get_note(note_id=999, winery_id=100)


# =============================================================================
# get_notes_for_fermentation
# =============================================================================


class TestGetNotesForFermentation:

    @pytest.mark.asyncio
    async def test_returns_list_of_notes(self):
        service, repo = _make_service()
        notes = [_make_note(id=1), _make_note(id=2)]
        repo.get_by_fermentation.return_value = notes

        result = await service.get_notes_for_fermentation(
            fermentation_id=10, winery_id=100
        )

        assert result == notes
        repo.get_by_fermentation.assert_called_once_with(
            fermentation_id=10, winery_id=100
        )

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_notes(self):
        service, repo = _make_service()
        repo.get_by_fermentation.return_value = []

        result = await service.get_notes_for_fermentation(
            fermentation_id=10, winery_id=100
        )

        assert result == []


# =============================================================================
# update_note
# =============================================================================


class TestUpdateNote:

    @pytest.mark.asyncio
    async def test_updates_note_successfully(self):
        service, repo = _make_service()
        updated = _make_note(note_text="Updated text")
        repo.update.return_value = updated

        result = await service.update_note(
            note_id=1,
            winery_id=100,
            note_text="Updated text",
        )

        assert result.note_text == "Updated text"
        repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_update_returns_none(self):
        service, repo = _make_service()
        repo.update.return_value = None

        with pytest.raises(FermentationNoteNotFoundError):
            await service.update_note(
                note_id=999,
                winery_id=100,
                note_text="Updated text",
            )

    @pytest.mark.asyncio
    async def test_passes_partial_update_dto(self):
        service, repo = _make_service()
        repo.update.return_value = _make_note()

        await service.update_note(
            note_id=1,
            winery_id=100,
            note_text="New text",
            action_taken=None,
        )

        call_args = repo.update.call_args
        dto = call_args.kwargs["data"]
        assert dto.note_text == "New text"
        assert dto.action_taken is None


# =============================================================================
# delete_note
# =============================================================================


class TestDeleteNote:

    @pytest.mark.asyncio
    async def test_deletes_note_successfully(self):
        service, repo = _make_service()
        repo.delete.return_value = True

        # Should not raise
        await service.delete_note(note_id=1, winery_id=100)

        repo.delete.assert_called_once_with(note_id=1, winery_id=100)

    @pytest.mark.asyncio
    async def test_raises_not_found_when_delete_returns_false(self):
        service, repo = _make_service()
        repo.delete.return_value = False

        with pytest.raises(FermentationNoteNotFoundError):
            await service.delete_note(note_id=999, winery_id=100)

"""
Unit tests for FermentationNoteRouter — API Layer (TDD).

Tests the note_router.py API endpoints with mocked service dependencies.
Written before the router implementation to drive the design.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.domain.enums.user_role import UserRole
from src.modules.fermentation.src.domain.entities.fermentation_note import (
    FermentationNote,
)
from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
    FermentationNoteNotFoundError,
)

# =============================================================================
# Helpers
# =============================================================================


def _make_user(winery_id: int = 100, user_id: int = 5) -> UserContext:
    return UserContext(
        user_id=user_id,
        email="winemaker@test.com",
        role=UserRole.WINEMAKER,
        winery_id=winery_id,
    )


def _make_note(**kwargs) -> FermentationNote:
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


# =============================================================================
# POST /fermentations/{fermentation_id}/notes
# =============================================================================


class TestAddNote:

    @pytest.mark.asyncio
    async def test_create_note_returns_201_with_note_data(self):
        from src.modules.fermentation.src.api.routers.note_router import add_note
        from src.modules.fermentation.src.api.schemas.note_schemas import (
            NoteCreateRequest,
        )

        service = AsyncMock()
        service.add_note.return_value = _make_note()

        body = NoteCreateRequest(
            note_text="Initial fermentation looks good",
            action_taken="Checked temperature",
        )
        user = _make_user()

        result = await add_note(
            fermentation_id=10,
            body=body,
            current_user=user,
            service=service,
        )

        assert result.id == 1
        assert result.note_text == "Initial fermentation looks good"
        service.add_note.assert_called_once_with(
            fermentation_id=10,
            winery_id=100,
            note_text="Initial fermentation looks good",
            action_taken="Checked temperature",
            created_by_user_id=5,
        )

    @pytest.mark.asyncio
    async def test_create_note_raises_404_when_fermentation_not_found(self):
        from fastapi import HTTPException
        from src.modules.fermentation.src.api.routers.note_router import add_note
        from src.modules.fermentation.src.api.schemas.note_schemas import (
            NoteCreateRequest,
        )
        from src.modules.fermentation.src.repository_component.errors import (
            EntityNotFoundError,
        )

        service = AsyncMock()
        service.add_note.side_effect = EntityNotFoundError("Fermentation not found")

        body = NoteCreateRequest(
            note_text="Some note",
            action_taken="Some action",
        )
        user = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await add_note(
                fermentation_id=999,
                body=body,
                current_user=user,
                service=service,
            )

        assert exc_info.value.status_code == 404


# =============================================================================
# GET /fermentations/{fermentation_id}/notes
# =============================================================================


class TestListNotes:

    @pytest.mark.asyncio
    async def test_list_notes_returns_list(self):
        from src.modules.fermentation.src.api.routers.note_router import list_notes

        service = AsyncMock()
        notes = [_make_note(id=1), _make_note(id=2)]
        service.get_notes_for_fermentation.return_value = notes

        user = _make_user()
        result = await list_notes(
            fermentation_id=10,
            current_user=user,
            service=service,
        )

        assert len(result.items) == 2
        service.get_notes_for_fermentation.assert_called_once_with(
            fermentation_id=10,
            winery_id=100,
        )

    @pytest.mark.asyncio
    async def test_list_notes_returns_empty_list(self):
        from src.modules.fermentation.src.api.routers.note_router import list_notes

        service = AsyncMock()
        service.get_notes_for_fermentation.return_value = []

        user = _make_user()
        result = await list_notes(
            fermentation_id=10,
            current_user=user,
            service=service,
        )

        assert result.items == []


# =============================================================================
# GET /notes/{note_id}
# =============================================================================


class TestGetNote:

    @pytest.mark.asyncio
    async def test_get_note_returns_note(self):
        from src.modules.fermentation.src.api.routers.note_router import get_note

        service = AsyncMock()
        service.get_note.return_value = _make_note(id=1)

        user = _make_user()
        result = await get_note(
            note_id=1,
            current_user=user,
            service=service,
        )

        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_note_raises_404_when_not_found(self):
        from fastapi import HTTPException
        from src.modules.fermentation.src.api.routers.note_router import get_note

        service = AsyncMock()
        service.get_note.side_effect = FermentationNoteNotFoundError(
            "Note 999 not found"
        )

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await get_note(
                note_id=999,
                current_user=user,
                service=service,
            )

        assert exc_info.value.status_code == 404


# =============================================================================
# PATCH /notes/{note_id}
# =============================================================================


class TestUpdateNote:

    @pytest.mark.asyncio
    async def test_update_note_returns_updated_data(self):
        from src.modules.fermentation.src.api.routers.note_router import update_note
        from src.modules.fermentation.src.api.schemas.note_schemas import (
            NoteUpdateRequest,
        )

        service = AsyncMock()
        service.update_note.return_value = _make_note(note_text="Updated text")

        body = NoteUpdateRequest(note_text="Updated text")
        user = _make_user()
        result = await update_note(
            note_id=1,
            body=body,
            current_user=user,
            service=service,
        )

        assert result.note_text == "Updated text"

    @pytest.mark.asyncio
    async def test_update_note_raises_404_when_not_found(self):
        from fastapi import HTTPException
        from src.modules.fermentation.src.api.routers.note_router import update_note
        from src.modules.fermentation.src.api.schemas.note_schemas import (
            NoteUpdateRequest,
        )

        service = AsyncMock()
        service.update_note.side_effect = FermentationNoteNotFoundError("Not found")

        body = NoteUpdateRequest(note_text="Updated text")
        user = _make_user()

        with pytest.raises(HTTPException) as exc_info:
            await update_note(
                note_id=999,
                body=body,
                current_user=user,
                service=service,
            )

        assert exc_info.value.status_code == 404


# =============================================================================
# DELETE /notes/{note_id}
# =============================================================================


class TestDeleteNote:

    @pytest.mark.asyncio
    async def test_delete_note_succeeds(self):
        from src.modules.fermentation.src.api.routers.note_router import delete_note

        service = AsyncMock()
        service.delete_note.return_value = None

        user = _make_user()
        # Should not raise
        result = await delete_note(
            note_id=1,
            current_user=user,
            service=service,
        )

        service.delete_note.assert_called_once_with(note_id=1, winery_id=100)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_note_raises_404_when_not_found(self):
        from fastapi import HTTPException
        from src.modules.fermentation.src.api.routers.note_router import delete_note

        service = AsyncMock()
        service.delete_note.side_effect = FermentationNoteNotFoundError("Not found")

        user = _make_user()
        with pytest.raises(HTTPException) as exc_info:
            await delete_note(
                note_id=999,
                current_user=user,
                service=service,
            )

        assert exc_info.value.status_code == 404

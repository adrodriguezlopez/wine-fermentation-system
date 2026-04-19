"""
Note Router — REST API for FermentationNote.

Endpoints:
    POST   /api/v1/fermentations/{fermentation_id}/notes  → add note
    GET    /api/v1/fermentations/{fermentation_id}/notes  → list notes
    GET    /api/v1/notes/{note_id}                        → get single note
    PATCH  /api/v1/notes/{note_id}                        → update note
    DELETE /api/v1/notes/{note_id}                        → soft delete
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker
from src.modules.fermentation.src.api.dependencies import get_db_session
from src.modules.fermentation.src.api.schemas.note_schemas import (
    NoteCreateRequest,
    NoteUpdateRequest,
    NoteResponse,
    NoteListResponse,
)
from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
    FermentationNoteService,
    FermentationNoteNotFoundError,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError
from src.shared.infra.repository.fastapi_session_manager import FastAPISessionManager

router = APIRouter(tags=["fermentation-notes"])


def _get_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FermentationNoteService:
    session_manager = FastAPISessionManager(session)
    repo: IFermentationNoteRepository = FermentationNoteRepository(session_manager)
    return FermentationNoteService(note_repo=repo)


# =============================================================================
# POST /fermentations/{fermentation_id}/notes
# =============================================================================

@router.post(
    "/fermentations/{fermentation_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to a fermentation",
    description=(
        "Attaches a free-text observation and action record to an active "
        "fermentation. The timestamp is recorded automatically."
    ),
)
async def add_note(
    fermentation_id: Annotated[int, Path(gt=0)],
    body: NoteCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> NoteResponse:
    try:
        note = await service.add_note(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id,
            note_text=body.note_text,
            action_taken=body.action_taken,
            created_by_user_id=current_user.user_id,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return NoteResponse.model_validate(note)


# =============================================================================
# GET /fermentations/{fermentation_id}/notes
# =============================================================================

@router.get(
    "/fermentations/{fermentation_id}/notes",
    response_model=NoteListResponse,
    status_code=status.HTTP_200_OK,
    summary="List notes for a fermentation",
)
async def list_notes(
    fermentation_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> NoteListResponse:
    notes = await service.get_notes_for_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
    )
    return NoteListResponse(items=[NoteResponse.model_validate(n) for n in notes])


# =============================================================================
# GET /notes/{note_id}
# =============================================================================

@router.get(
    "/notes/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single fermentation note",
)
async def get_note(
    note_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> NoteResponse:
    try:
        note = await service.get_note(note_id=note_id, winery_id=current_user.winery_id)
    except FermentationNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return NoteResponse.model_validate(note)


# =============================================================================
# PATCH /notes/{note_id}
# =============================================================================

@router.patch(
    "/notes/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a fermentation note",
)
async def update_note(
    note_id: Annotated[int, Path(gt=0)],
    body: NoteUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> NoteResponse:
    try:
        note = await service.update_note(
            note_id=note_id,
            winery_id=current_user.winery_id,
            note_text=body.note_text,
            action_taken=body.action_taken,
        )
    except FermentationNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return NoteResponse.model_validate(note)


# =============================================================================
# DELETE /notes/{note_id}
# =============================================================================

@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a fermentation note",
)
async def delete_note(
    note_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> None:
    try:
        await service.delete_note(note_id=note_id, winery_id=current_user.winery_id)
    except FermentationNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )

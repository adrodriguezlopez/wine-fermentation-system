# Adding `FermentationNote` End-to-End — Implementation Guide

## Context read-out (before any code)

**NIVEL 1 — `project-context.md`** tells me:
- System is a modular monolith, Clean Architecture, strict TDD.
- Fermentation module: ✅ COMPLETE, ~728 tests passing.
- All layers (Domain → Repository → Service → API) are implemented.

**NIVEL 2 — `module-context.md`** tells me:
- `FermentationNoteRepository` is ✅ COMPLETE (19 unit + 20 integration tests).
- The **service layer and API router for FermentationNote do not exist yet** — no `note_service.py`, no `note_router.py`, no `note_schemas.py`.
- The module uses `api/`, `repository_component/`, `service_component/` naming.
- `main.py` registers routers explicitly.

**NIVEL 3 — `domain-model-guide.md`** tells me:
- `FermentationNote` is a documented first-class entity: free-text note (`note_text`), `action_taken`, `created_by_user_id`, belongs to a `Fermentation`.
- `BaseEntity` provides `id`, `created_at`, `updated_at`.
- `FermentationNote` already exists in `src/domain/entities/fermentation_note.py`.
- DTOs (`FermentationNoteCreate`, `FermentationNoteUpdate`) already exist.
- Repository interface (`IFermentationNoteRepository`) already exists.
- Repository implementation (`FermentationNoteRepository`) already exists.

**NIVEL 4 — Actual code** confirms:
- Entity has `note_text` (Text), `action_taken` (String 255), `created_by_user_id`, `fermentation_id`, `is_deleted`.
- `created_at` comes from `BaseEntity` — this IS the timestamp field.
- Existing `action_router.py` and `action_service.py` are the best reference patterns (both were added recently using the same architecture).

---

## What already exists vs. what you need to build

| Layer | Status |
|-------|--------|
| Domain entity (`FermentationNote`) | ✅ Exists |
| DTOs (`FermentationNoteCreate/Update`) | ✅ Exists |
| Repository interface (`IFermentationNoteRepository`) | ✅ Exists |
| Repository implementation (`FermentationNoteRepository`) | ✅ Exists — 19 unit + 20 integration tests |
| **Service layer** | ❌ Missing — build this |
| **API schemas** | ❌ Missing — build this |
| **API router** | ❌ Missing — build this |
| **Tests (service + API)** | ❌ Missing — write before implementing |
| **`main.py` registration** | ❌ Missing |
| **Alembic migration** | ✅ Not needed — table already exists (created during repository phase) |

> **One important design note before we start**: The existing `FermentationNoteCreate` DTO requires `action_taken` as a mandatory field. This is a domain-layer contract that was established when the repository was built. For the API, we'll expose that field in the request schema. If you want to make `action_taken` optional (i.e., allow "pure observation" notes), that's a legitimate business rule change — but it requires changing the DTO and existing tests. Don't sneak that in silently; make it an explicit decision.

---

## Step 1 — Write the failing service tests first (TDD: Red)

Create `src/modules/fermentation/tests/unit/service_component/test_fermentation_note_service.py`:

```python
"""
Unit tests for FermentationNoteService.
TDD: written BEFORE the service implementation.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_note(
    note_id: int = 1,
    fermentation_id: int = 10,
    note_text: str = "Brix dropped 2 points overnight",
    action_taken: str = "Added yeast nutrients",
    created_by_user_id: int = 42,
) -> FermentationNote:
    note = MagicMock(spec=FermentationNote)
    note.id = note_id
    note.fermentation_id = fermentation_id
    note.note_text = note_text
    note.action_taken = action_taken
    note.created_by_user_id = created_by_user_id
    note.created_at = datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc)
    note.is_deleted = False
    return note


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=IFermentationNoteRepository)


@pytest.fixture
def service(mock_repo: AsyncMock):
    # Import here so the test file fails cleanly until the service exists
    from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
        FermentationNoteService,
    )
    return FermentationNoteService(repository=mock_repo)


# ---------------------------------------------------------------------------
# create_note
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_note_delegates_to_repository(service, mock_repo):
    """Service.create_note calls repo.create with correct args and returns result."""
    expected = _make_note()
    mock_repo.create.return_value = expected

    result = await service.create_note(
        fermentation_id=10,
        winery_id=5,
        note_text="Brix dropped 2 points overnight",
        action_taken="Added yeast nutrients",
        created_by_user_id=42,
    )

    mock_repo.create.assert_called_once()
    call_kwargs = mock_repo.create.call_args
    assert call_kwargs.kwargs["fermentation_id"] == 10
    assert call_kwargs.kwargs["winery_id"] == 5
    assert result is expected


@pytest.mark.asyncio
async def test_create_note_raises_on_empty_text(service, mock_repo):
    """Service validates note_text before hitting the repository."""
    with pytest.raises(ValueError, match="note_text"):
        await service.create_note(
            fermentation_id=10,
            winery_id=5,
            note_text="   ",          # blank
            action_taken="Something",
            created_by_user_id=42,
        )
    mock_repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# get_note
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_note_returns_entity_when_found(service, mock_repo):
    expected = _make_note()
    mock_repo.get_by_id.return_value = expected

    result = await service.get_note(note_id=1, winery_id=5)

    mock_repo.get_by_id.assert_called_once_with(note_id=1, winery_id=5)
    assert result is expected


@pytest.mark.asyncio
async def test_get_note_raises_not_found_when_missing(service, mock_repo):
    from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
        FermentationNoteNotFoundError,
    )
    mock_repo.get_by_id.return_value = None

    with pytest.raises(FermentationNoteNotFoundError):
        await service.get_note(note_id=999, winery_id=5)


# ---------------------------------------------------------------------------
# list_notes_for_fermentation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_notes_returns_all_for_fermentation(service, mock_repo):
    notes = [_make_note(i) for i in range(3)]
    mock_repo.get_by_fermentation.return_value = notes

    result = await service.list_notes_for_fermentation(
        fermentation_id=10, winery_id=5
    )

    mock_repo.get_by_fermentation.assert_called_once_with(
        fermentation_id=10, winery_id=5
    )
    assert result == notes


@pytest.mark.asyncio
async def test_list_notes_returns_empty_list_when_none(service, mock_repo):
    mock_repo.get_by_fermentation.return_value = []

    result = await service.list_notes_for_fermentation(
        fermentation_id=10, winery_id=5
    )

    assert result == []


# ---------------------------------------------------------------------------
# update_note
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_note_delegates_to_repository(service, mock_repo):
    updated = _make_note(note_text="Revised observation")
    mock_repo.update.return_value = updated

    result = await service.update_note(
        note_id=1,
        winery_id=5,
        note_text="Revised observation",
        action_taken=None,
    )

    mock_repo.update.assert_called_once()
    assert result is updated


@pytest.mark.asyncio
async def test_update_note_raises_not_found_when_missing(service, mock_repo):
    from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
        FermentationNoteNotFoundError,
    )
    mock_repo.update.return_value = None

    with pytest.raises(FermentationNoteNotFoundError):
        await service.update_note(
            note_id=999, winery_id=5, note_text="new text", action_taken=None
        )


# ---------------------------------------------------------------------------
# delete_note
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_note_returns_true_when_found(service, mock_repo):
    mock_repo.delete.return_value = True

    result = await service.delete_note(note_id=1, winery_id=5)

    mock_repo.delete.assert_called_once_with(note_id=1, winery_id=5)
    assert result is True


@pytest.mark.asyncio
async def test_delete_note_raises_not_found_when_missing(service, mock_repo):
    from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
        FermentationNoteNotFoundError,
    )
    mock_repo.delete.return_value = False

    with pytest.raises(FermentationNoteNotFoundError):
        await service.delete_note(note_id=999, winery_id=5)
```

Run it — confirm red:
```powershell
cd src/modules/fermentation
poetry run pytest tests/unit/service_component/test_fermentation_note_service.py -v
# Expected: ImportError / 10 failures — service does not exist yet
```

---

## Step 2 — Implement `FermentationNoteService` (Green)

Create `src/modules/fermentation/src/service_component/services/fermentation_note_service.py`:

```python
"""
FermentationNoteService — business logic for fermentation notes.

Winemakers attach free-text notes to any fermentation during the process.
Each note captures the observation text, the action taken, the author, and
a timestamp (created_at, provided automatically by BaseEntity).

Design decisions:
  - Service depends on IFermentationNoteRepository (interface), never on the
    concrete SQLAlchemy implementation (DIP).
  - Validation of note_text happens here, not in the repository, to keep the
    repo a thin persistence adapter.
  - FermentationNoteNotFoundError is a domain-level signal; the API layer maps
    it to HTTP 404.
"""

from typing import List, Optional

from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.shared.wine_fermentator_logging import get_logger

logger = get_logger(__name__)


class FermentationNoteNotFoundError(Exception):
    """Raised when a note cannot be found or does not belong to the winery."""


class FermentationNoteService:
    """
    Orchestrates note creation, retrieval, update, and deletion.

    Accepts IFermentationNoteRepository via constructor injection so that
    unit tests can pass in a mock without touching the database.
    """

    def __init__(self, repository: IFermentationNoteRepository) -> None:
        self._repo = repository

    # ------------------------------------------------------------------
    # Command: create a note
    # ------------------------------------------------------------------

    async def create_note(
        self,
        fermentation_id: int,
        winery_id: int,
        note_text: str,
        action_taken: str,
        created_by_user_id: int,
    ) -> FermentationNote:
        """
        Attach a new note to a fermentation.

        Raises:
            ValueError: If note_text or action_taken are blank.
            EntityNotFoundError (from repo): If fermentation doesn't belong to winery.
        """
        if not note_text or not note_text.strip():
            raise ValueError("note_text cannot be empty")
        if not action_taken or not action_taken.strip():
            raise ValueError("action_taken cannot be empty")

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
            "fermentation_note_created",
            note_id=note.id,
            fermentation_id=fermentation_id,
            winery_id=winery_id,
            user_id=created_by_user_id,
        )
        return note

    # ------------------------------------------------------------------
    # Query: single note
    # ------------------------------------------------------------------

    async def get_note(
        self,
        note_id: int,
        winery_id: int,
    ) -> FermentationNote:
        """
        Retrieve a single note by ID, scoped to the winery.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or
                belongs to a different winery.
        """
        note = await self._repo.get_by_id(note_id=note_id, winery_id=winery_id)
        if note is None:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found in winery {winery_id}"
            )
        return note

    # ------------------------------------------------------------------
    # Query: all notes for a fermentation
    # ------------------------------------------------------------------

    async def list_notes_for_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
    ) -> List[FermentationNote]:
        """
        Return all active notes for a fermentation, ordered by created_at DESC.
        Returns an empty list if the fermentation has no notes.
        """
        return await self._repo.get_by_fermentation(
            fermentation_id=fermentation_id,
            winery_id=winery_id,
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
        Partial update of a note's text and/or action_taken.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or
                belongs to a different winery.
        """
        dto = FermentationNoteUpdate(note_text=note_text, action_taken=action_taken)
        note = await self._repo.update(
            note_id=note_id,
            winery_id=winery_id,
            data=dto,
        )
        if note is None:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found in winery {winery_id}"
            )

        logger.info(
            "fermentation_note_updated",
            note_id=note_id,
            winery_id=winery_id,
        )
        return note

    # ------------------------------------------------------------------
    # Command: delete a note
    # ------------------------------------------------------------------

    async def delete_note(
        self,
        note_id: int,
        winery_id: int,
    ) -> bool:
        """
        Soft-delete a note.

        Raises:
            FermentationNoteNotFoundError: If the note does not exist or
                belongs to a different winery.
        """
        deleted = await self._repo.delete(note_id=note_id, winery_id=winery_id)
        if not deleted:
            raise FermentationNoteNotFoundError(
                f"Note {note_id} not found in winery {winery_id}"
            )

        logger.info(
            "fermentation_note_deleted",
            note_id=note_id,
            winery_id=winery_id,
        )
        return True
```

Confirm green:
```powershell
poetry run pytest tests/unit/service_component/test_fermentation_note_service.py -v
# Expected: 10 passed
```

---

## Step 3 — Write failing API tests (TDD: Red)

Create `src/modules/fermentation/tests/api/test_fermentation_note_router.py`:

```python
"""
API tests for FermentationNote endpoints.
TDD: written BEFORE the router implementation.

Uses FastAPI TestClient with mocked FermentationNoteService.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_note_entity(note_id=1, fermentation_id=10, note_text="Test note",
                       action_taken="Add nutrients", created_by_user_id=42):
    note = MagicMock(spec=FermentationNote)
    note.id = note_id
    note.fermentation_id = fermentation_id
    note.note_text = note_text
    note.action_taken = action_taken
    note.created_by_user_id = created_by_user_id
    note.created_at = datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc)
    note.updated_at = datetime(2026, 4, 18, 10, 0, 0, tzinfo=timezone.utc)
    note.is_deleted = False
    note.winery_id = 5
    return note


AUTH_HEADERS = {"Authorization": "Bearer test-token"}
WINERY_ID = 5
USER_ID = 42

MOCK_USER = MagicMock()
MOCK_USER.winery_id = WINERY_ID
MOCK_USER.user_id = USER_ID


@pytest.fixture
def client():
    from src.modules.fermentation.src.main import app
    from src.shared.auth.infra.api.dependencies import require_winemaker, require_admin
    app.dependency_overrides[require_winemaker] = lambda: MOCK_USER
    app.dependency_overrides[require_admin] = lambda: MOCK_USER
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /api/v1/fermentations/{fermentation_id}/notes
# ---------------------------------------------------------------------------

def test_create_note_returns_201(client):
    note = _make_note_entity()
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.create_note = AsyncMock(return_value=note)

        resp = client.post(
            "/api/v1/fermentations/10/notes",
            json={
                "note_text": "Brix dropped fast",
                "action_taken": "Added nutrients",
            },
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["note_text"] == "Test note"
    assert data["fermentation_id"] == 10


def test_create_note_returns_422_when_text_blank(client):
    resp = client.post(
        "/api/v1/fermentations/10/notes",
        json={"note_text": "", "action_taken": "Something"},
        headers=AUTH_HEADERS,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/v1/fermentations/{fermentation_id}/notes
# ---------------------------------------------------------------------------

def test_list_notes_returns_200(client):
    notes = [_make_note_entity(i) for i in range(3)]
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.list_notes_for_fermentation = AsyncMock(return_value=notes)

        resp = client.get(
            "/api/v1/fermentations/10/notes",
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, list)
    assert len(body) == 3


# ---------------------------------------------------------------------------
# GET /api/v1/notes/{note_id}
# ---------------------------------------------------------------------------

def test_get_note_returns_200_when_found(client):
    note = _make_note_entity()
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.get_note = AsyncMock(return_value=note)

        resp = client.get("/api/v1/notes/1", headers=AUTH_HEADERS)

    assert resp.status_code == 200


def test_get_note_returns_404_when_missing(client):
    from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
        FermentationNoteNotFoundError,
    )
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.get_note = AsyncMock(side_effect=FermentationNoteNotFoundError("not found"))

        resp = client.get("/api/v1/notes/999", headers=AUTH_HEADERS)

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /api/v1/notes/{note_id}
# ---------------------------------------------------------------------------

def test_update_note_returns_200(client):
    note = _make_note_entity(note_text="Updated text")
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.update_note = AsyncMock(return_value=note)

        resp = client.patch(
            "/api/v1/notes/1",
            json={"note_text": "Updated text"},
            headers=AUTH_HEADERS,
        )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /api/v1/notes/{note_id}
# ---------------------------------------------------------------------------

def test_delete_note_returns_204(client):
    svc_path = (
        "src.modules.fermentation.src.api.routers.fermentation_note_router"
        ".FermentationNoteService"
    )
    with patch(svc_path) as MockService:
        instance = MockService.return_value
        instance.delete_note = AsyncMock(return_value=True)

        resp = client.delete("/api/v1/notes/1", headers=AUTH_HEADERS)

    assert resp.status_code == 204
```

Run to confirm red:
```powershell
poetry run pytest tests/api/test_fermentation_note_router.py -v
# Expected: ImportError / failures — router does not exist yet
```

---

## Step 4 — Implement the API schemas and router (Green)

### 4a. API schemas

Create `src/modules/fermentation/src/api/schemas/fermentation_note_schemas.py`:

```python
"""
Request / Response schemas for FermentationNote.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Request schemas
# =============================================================================

class FermentationNoteCreateRequest(BaseModel):
    """Payload for POST /fermentations/{fermentation_id}/notes."""

    note_text: str = Field(
        ..., min_length=1, max_length=10_000,
        description="Free-text observation or note written by the winemaker"
    )
    action_taken: str = Field(
        ..., min_length=1, max_length=255,
        description="Brief description of the action taken (required)"
    )


class FermentationNoteUpdateRequest(BaseModel):
    """Payload for PATCH /notes/{note_id} — all fields optional."""

    note_text: Optional[str] = Field(
        None, min_length=1, max_length=10_000,
        description="Updated note text"
    )
    action_taken: Optional[str] = Field(
        None, min_length=1, max_length=255,
        description="Updated action taken"
    )


# =============================================================================
# Response schema
# =============================================================================

class FermentationNoteResponse(BaseModel):
    """Serialized FermentationNote returned from all endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fermentation_id: int
    note_text: str
    action_taken: str
    created_by_user_id: int
    created_at: datetime   # timestamp — provided by BaseEntity
    updated_at: datetime
```

### 4b. API router

Create `src/modules/fermentation/src/api/routers/fermentation_note_router.py`:

```python
"""
FermentationNote Router — REST API for winemaker notes on fermentations.

Endpoints:
    POST   /api/v1/fermentations/{fermentation_id}/notes   → add a note
    GET    /api/v1/fermentations/{fermentation_id}/notes   → list notes
    GET    /api/v1/notes/{note_id}                         → get single note
    PATCH  /api/v1/notes/{note_id}                         → update note
    DELETE /api/v1/notes/{note_id}                         → soft-delete (admin)
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import require_winemaker, require_admin
from src.modules.fermentation.src.api.dependencies import get_db_session
from src.modules.fermentation.src.api.schemas.fermentation_note_schemas import (
    FermentationNoteCreateRequest,
    FermentationNoteUpdateRequest,
    FermentationNoteResponse,
)
from src.modules.fermentation.src.service_component.services.fermentation_note_service import (
    FermentationNoteService,
    FermentationNoteNotFoundError,
)
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)

router = APIRouter(tags=["fermentation-notes"])


def _get_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> FermentationNoteService:
    return FermentationNoteService(repository=FermentationNoteRepository(session))


# =============================================================================
# POST /fermentations/{fermentation_id}/notes
# =============================================================================

@router.post(
    "/fermentations/{fermentation_id}/notes",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to a fermentation",
    description=(
        "Attaches a free-text note to a fermentation. "
        "The timestamp is recorded automatically (created_at). "
        "The author is taken from the authenticated user's context."
    ),
)
async def create_note(
    fermentation_id: Annotated[int, Path(gt=0)],
    body: FermentationNoteCreateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> FermentationNoteResponse:
    note = await service.create_note(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
        note_text=body.note_text,
        action_taken=body.action_taken,
        created_by_user_id=current_user.user_id,
    )
    return FermentationNoteResponse.model_validate(note)


# =============================================================================
# GET /fermentations/{fermentation_id}/notes
# =============================================================================

@router.get(
    "/fermentations/{fermentation_id}/notes",
    response_model=List[FermentationNoteResponse],
    status_code=status.HTTP_200_OK,
    summary="List notes for a fermentation",
    description="Returns all notes for the fermentation, ordered newest first.",
)
async def list_notes(
    fermentation_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> List[FermentationNoteResponse]:
    notes = await service.list_notes_for_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
    )
    return [FermentationNoteResponse.model_validate(n) for n in notes]


# =============================================================================
# GET /notes/{note_id}
# =============================================================================

@router.get(
    "/notes/{note_id}",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single note",
)
async def get_note(
    note_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> FermentationNoteResponse:
    try:
        note = await service.get_note(note_id=note_id, winery_id=current_user.winery_id)
    except FermentationNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return FermentationNoteResponse.model_validate(note)


# =============================================================================
# PATCH /notes/{note_id}
# =============================================================================

@router.patch(
    "/notes/{note_id}",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a note",
    description="Partial update — only supplied fields are changed.",
)
async def update_note(
    note_id: Annotated[int, Path(gt=0)],
    body: FermentationNoteUpdateRequest,
    current_user: Annotated[UserContext, Depends(require_winemaker)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> FermentationNoteResponse:
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
    return FermentationNoteResponse.model_validate(note)


# =============================================================================
# DELETE /notes/{note_id}
# =============================================================================

@router.delete(
    "/notes/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note (admin only)",
    description="Soft-deletes the note. The record remains in the database with is_deleted=True.",
)
async def delete_note(
    note_id: Annotated[int, Path(gt=0)],
    current_user: Annotated[UserContext, Depends(require_admin)],
    service: Annotated[FermentationNoteService, Depends(_get_service)],
) -> None:
    try:
        await service.delete_note(note_id=note_id, winery_id=current_user.winery_id)
    except FermentationNoteNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
```

Confirm green:
```powershell
poetry run pytest tests/api/test_fermentation_note_router.py -v
# Expected: 7 passed
```

---

## Step 5 — Register the router in `main.py`

Edit `src/modules/fermentation/src/main.py`. Add the import alongside the other routers:

```python
# Add this import with the other router imports
from src.modules.fermentation.src.api.routers.fermentation_note_router import router as fermentation_note_router
```

Then register it in `_setup_routes()` (after `action_router`):

```python
app.include_router(fermentation_note_router, prefix=API_V1_PREFIX, tags=["fermentation-notes"])
```

---

## Step 6 — Run the full suite to confirm no regressions

```powershell
cd src/modules/fermentation
poetry run pytest tests/ -v --tb=short
# Expected: all existing ~728 + 17 new tests passing
```

---

## Step 7 — No new Alembic migration needed

The `fermentation_notes` table was already created during the repository phase (the repository and integration tests are all ✅). Run `alembic current` to confirm:

```powershell
alembic current
# Should show head — no pending migrations
```

If for some reason the table doesn't exist in your environment (fresh DB), generate the migration:

```powershell
alembic revision --autogenerate -m "008_fermentation_note_table"
alembic upgrade head
```

---

## Step 8 — Update `.ai-context/module-context.md`

Update the Component Summary table and Completed Components:

```markdown
| Service Layer | ✅ Complete | FermentationService, SampleService, ValidationOrchestrator, ETLService, PatternAnalysisService, **FermentationNoteService** |
| API Layer     | ✅ Complete | 17 endpoints + **5 FermentationNote endpoints** |
| Total tests   | ✅          | **~745 passing** (728 + 17 new) |
```

Also add `FermentationNoteService` to the Service Component bullet list and `fermentation_note_router.py` to the API Layer bullet list.

---

## Architecture summary — how all pieces fit together

```
HTTP Request
     │
     ▼
fermentation_note_router.py       ← FastAPI router (api/)
  Uses: FermentationNoteCreateRequest / FermentationNoteResponse (Pydantic)
  Calls: FermentationNoteService (injected via Depends)
     │
     ▼
fermentation_note_service.py      ← Business logic (service_component/)
  Depends on: IFermentationNoteRepository (interface — domain/)
  Raises: FermentationNoteNotFoundError (domain signal)
     │
     ▼
fermentation_note_repository.py   ← SQLAlchemy impl (repository_component/)
  Implements: IFermentationNoteRepository
  Uses: FermentationNote entity, FermentationNoteCreate/Update DTOs
     │
     ▼
PostgreSQL  fermentation_notes table
  Columns: id, fermentation_id, created_by_user_id, note_text,
           action_taken, is_deleted, created_at, updated_at
```

**Dependency direction**: Router → Service → Interface ← Repository.  
The service never imports `FermentationNoteRepository` directly — only the DI function in the router does.  
This means you can unit-test the service with a mock, and the router tests can mock the service class.

---

## File checklist — complete picture

| File | Action |
|------|--------|
| `src/domain/entities/fermentation_note.py` | ✅ Already exists — no changes |
| `src/domain/dtos/fermentation_note_dtos.py` | ✅ Already exists — no changes |
| `src/domain/repositories/fermentation_note_repository_interface.py` | ✅ Already exists — no changes |
| `src/repository_component/repositories/fermentation_note_repository.py` | ✅ Already exists — no changes |
| `src/service_component/services/fermentation_note_service.py` | 🆕 **Create (Step 2)** |
| `src/api/schemas/fermentation_note_schemas.py` | 🆕 **Create (Step 4a)** |
| `src/api/routers/fermentation_note_router.py` | 🆕 **Create (Step 4b)** |
| `src/main.py` | ✏️ **Edit — add import + include_router (Step 5)** |
| `tests/unit/service_component/test_fermentation_note_service.py` | 🆕 **Create (Step 1)** |
| `tests/api/test_fermentation_note_router.py` | 🆕 **Create (Step 3)** |
| `alembic/versions/` | ✅ No new migration needed (table exists) |
| `.ai-context/module-context.md` | ✏️ **Update test counts + component list (Step 8)** |

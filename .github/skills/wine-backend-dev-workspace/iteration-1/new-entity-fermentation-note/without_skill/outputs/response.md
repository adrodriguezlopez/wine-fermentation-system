# Implementing the `FermentationNote` Entity — End-to-End Guide

This guide walks through adding a `FermentationNote` entity to the fermentation module of a FastAPI + SQLAlchemy (async) backend. The entity lets winemakers attach a free-text note to any fermentation, capturing a timestamp and the user who wrote it.

---

## Overview of the layers we will touch

| Layer | File(s) to create / edit |
|---|---|
| ORM Entity | `domain/entities/fermentation_note.py` |
| Parent entity | `domain/entities/fermentation.py` — add `notes` relationship |
| Domain DTOs | `domain/dtos/fermentation_note_dtos.py` |
| Repository interface | `domain/repositories/fermentation_note_repository_interface.py` |
| Repository implementation | `repository_component/repositories/fermentation_note_repository.py` |
| API request schemas | `api/schemas/requests/fermentation_note_requests.py` |
| API response schemas | `api/schemas/responses/fermentation_note_responses.py` |
| API router | `api/routers/fermentation_note_router.py` |
| App registration | `src/main.py` — include the new router |
| Database migration | `alembic/versions/XXX_create_fermentation_notes.py` |
| Tests | unit + integration tests |

---

## Step 1 — ORM Entity

Create `src/modules/fermentation/src/domain/entities/fermentation_note.py`:

```python
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation


class FermentationNote(BaseEntity):
    """
    A free-text note attached to a fermentation by a winemaker.

    Fields:
        fermentation_id  — FK to fermentations.id
        created_by_user_id — FK to users.id (the author)
        note_text        — free-text content (unlimited length via TEXT)
        is_deleted       — soft-delete flag

    Timestamps (inherited from BaseEntity):
        created_at  — when the note was written
        updated_at  — last edit timestamp
    """
    __tablename__ = "fermentation_notes"

    # Foreign Keys
    fermentation_id = Column(
        Integer, ForeignKey("fermentations.id"), nullable=False, index=True
    )
    created_by_user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False
    )

    # Note content
    note_text = Column(Text, nullable=False)

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="false")

    # Relationships
    fermentation: Mapped["Fermentation"] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation.Fermentation",
        back_populates="notes",
    )
```

Key design decisions:
- **`TEXT` column** — no arbitrary length cap on notes.
- **`created_at` from `BaseEntity`** — this is the "timestamp" that records when the note was written. No extra column needed.
- **`created_by_user_id`** — stores the author; read from the JWT context at the API layer, never accepted from the request body.
- **Soft delete** — notes are never physically removed; `is_deleted=True` hides them.

---

## Step 2 — Update the `Fermentation` entity

Add the `notes` back-reference so SQLAlchemy knows about the one-to-many:

```python
# domain/entities/fermentation.py  (additions only)

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote

class Fermentation(BaseEntity):
    # ... existing columns ...

    notes: Mapped[List["FermentationNote"]] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation_note.FermentationNote",
        back_populates="fermentation",
        cascade="all, delete-orphan",
        lazy="select",
    )
```

---

## Step 3 — Domain DTOs

Create `src/modules/fermentation/src/domain/dtos/fermentation_note_dtos.py`:

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class FermentationNoteCreate:
    """
    Internal DTO for creating a note.

    `created_by_user_id` is injected by the service layer from the auth
    context — never supplied by the client.
    """
    note_text: str
    created_by_user_id: int

    def __post_init__(self) -> None:
        if not self.note_text or not self.note_text.strip():
            raise ValueError("note_text is required and cannot be blank")
        if not isinstance(self.created_by_user_id, int) or self.created_by_user_id <= 0:
            raise ValueError("created_by_user_id must be a positive integer")
        self.note_text = self.note_text.strip()


@dataclass
class FermentationNoteUpdate:
    """Partial update DTO — only `note_text` is editable after creation."""
    note_text: Optional[str] = None

    def __post_init__(self) -> None:
        if self.note_text is not None:
            if not self.note_text.strip():
                raise ValueError("note_text cannot be blank")
            self.note_text = self.note_text.strip()

    def has_updates(self) -> bool:
        return self.note_text is not None
```

---

## Step 4 — Repository Interface

Create `src/modules/fermentation/src/domain/repositories/fermentation_note_repository_interface.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
    from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
        FermentationNoteCreate,
        FermentationNoteUpdate,
    )


class IFermentationNoteRepository(ABC):
    """
    Contract for fermentation note persistence.

    All mutating operations take `winery_id` and enforce multi-tenant
    isolation by joining through the parent fermentation table.
    """

    @abstractmethod
    async def create(
        self,
        fermentation_id: int,
        winery_id: int,
        data: "FermentationNoteCreate",
    ) -> "FermentationNote":
        """
        Persist a new note.

        Raises:
            EntityNotFoundError: fermentation does not exist or belongs to a
                                  different winery.
        """
        ...

    @abstractmethod
    async def get_by_id(
        self,
        note_id: int,
        winery_id: int,
    ) -> Optional["FermentationNote"]:
        """Return the note, or None if not found / wrong winery."""
        ...

    @abstractmethod
    async def list_by_fermentation(
        self,
        fermentation_id: int,
        winery_id: int,
    ) -> List["FermentationNote"]:
        """Return all non-deleted notes for a fermentation, newest first."""
        ...

    @abstractmethod
    async def update(
        self,
        note_id: int,
        winery_id: int,
        data: "FermentationNoteUpdate",
    ) -> Optional["FermentationNote"]:
        """Apply a partial update. Returns None if note not found."""
        ...

    @abstractmethod
    async def delete(
        self,
        note_id: int,
        winery_id: int,
    ) -> bool:
        """Soft-delete a note. Returns False if the note was not found."""
        ...
```

---

## Step 5 — Repository Implementation

Create `src/modules/fermentation/src/repository_component/repositories/fermentation_note_repository.py`:

```python
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError
from src.shared.infra.repository.base_repository import BaseRepository


class FermentationNoteRepository(BaseRepository, IFermentationNoteRepository):
    """SQLAlchemy async implementation of IFermentationNoteRepository."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _active_note_query(self, note_id: int, winery_id: int):
        """Base query: note exists, not deleted, fermentation belongs to winery."""
        return (
            select(FermentationNote)
            .join(Fermentation, FermentationNote.fermentation_id == Fermentation.id)
            .where(
                and_(
                    FermentationNote.id == note_id,
                    FermentationNote.is_deleted == False,
                    Fermentation.winery_id == winery_id,
                    Fermentation.is_deleted == False,
                )
            )
        )

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    async def create(
        self,
        fermentation_id: int,
        winery_id: int,
        data: FermentationNoteCreate,
    ) -> FermentationNote:
        session_cm = await self.get_session()
        async with session_cm as session:
            # Verify the fermentation exists and belongs to this winery
            fermentation = await session.scalar(
                select(Fermentation).where(
                    and_(
                        Fermentation.id == fermentation_id,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False,
                    )
                )
            )
            if fermentation is None:
                raise EntityNotFoundError(
                    f"Fermentation {fermentation_id} not found for winery {winery_id}"
                )

            note = FermentationNote(
                fermentation_id=fermentation_id,
                created_by_user_id=data.created_by_user_id,
                note_text=data.note_text,
                is_deleted=False,
            )
            session.add(note)
            await session.flush()
            await session.refresh(note)
            return note

    async def update(
        self,
        note_id: int,
        winery_id: int,
        data: FermentationNoteUpdate,
    ) -> Optional[FermentationNote]:
        session_cm = await self.get_session()
        async with session_cm as session:
            note = await session.scalar(self._active_note_query(note_id, winery_id))
            if note is None:
                return None
            if data.note_text is not None:
                note.note_text = data.note_text
            await session.flush()
            await session.refresh(note)
            return note

    async def delete(self, note_id: int, winery_id: int) -> bool:
        session_cm = await self.get_session()
        async with session_cm as session:
            note = await session.scalar(self._active_note_query(note_id, winery_id))
            if note is None:
                return False
            note.is_deleted = True
            await session.flush()
            return True

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    async def get_by_id(
        self, note_id: int, winery_id: int
    ) -> Optional[FermentationNote]:
        session_cm = await self.get_session()
        async with session_cm as session:
            return await session.scalar(self._active_note_query(note_id, winery_id))

    async def list_by_fermentation(
        self, fermentation_id: int, winery_id: int
    ) -> List[FermentationNote]:
        session_cm = await self.get_session()
        async with session_cm as session:
            result = await session.execute(
                select(FermentationNote)
                .join(Fermentation, FermentationNote.fermentation_id == Fermentation.id)
                .where(
                    and_(
                        FermentationNote.fermentation_id == fermentation_id,
                        FermentationNote.is_deleted == False,
                        Fermentation.winery_id == winery_id,
                        Fermentation.is_deleted == False,
                    )
                )
                .order_by(FermentationNote.created_at.desc())
            )
            return list(result.scalars().all())
```

---

## Step 6 — API Request Schemas

Create `src/modules/fermentation/src/api/schemas/requests/fermentation_note_requests.py`:

```python
from pydantic import BaseModel, Field


class FermentationNoteCreateRequest(BaseModel):
    """
    Body for POST /fermentations/{id}/notes

    The author (`created_by_user_id`) and timestamp (`created_at`) are
    derived from the JWT token and server clock respectively — not accepted
    from the client.
    """
    note_text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Free-text note from the winemaker",
    )


class FermentationNoteUpdateRequest(BaseModel):
    """Body for PATCH /fermentations/{fermentation_id}/notes/{note_id}"""
    note_text: str = Field(
        ...,
        min_length=1,
        max_length=10_000,
        description="Updated note text",
    )
```

---

## Step 7 — API Response Schemas

Create `src/modules/fermentation/src/api/schemas/responses/fermentation_note_responses.py`:

```python
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FermentationNoteResponse(BaseModel):
    """
    Serialized representation of a FermentationNote returned by the API.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Note unique identifier")
    fermentation_id: int = Field(..., description="Parent fermentation")
    created_by_user_id: int = Field(..., description="Author user ID")
    note_text: str = Field(..., description="Note content")
    created_at: datetime = Field(..., description="When the note was written")
    updated_at: datetime = Field(..., description="Last modification timestamp")

    @classmethod
    def from_entity(cls, note) -> "FermentationNoteResponse":
        return cls(
            id=note.id,
            fermentation_id=note.fermentation_id,
            created_by_user_id=note.created_by_user_id,
            note_text=note.note_text,
            created_at=note.created_at,
            updated_at=note.updated_at,
        )
```

---

## Step 8 — API Router

Create `src/modules/fermentation/src/api/routers/fermentation_note_router.py`:

```python
"""
FermentationNote endpoints.

All routes are nested under /fermentations/{fermentation_id}/notes.
Authentication: JWT required (require_winemaker for writes, get_current_user for reads).
Multi-tenancy: enforced at the repository layer via winery_id.
"""

from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.shared.auth.domain.dtos import UserContext
from src.shared.auth.infra.api.dependencies import get_current_user, require_winemaker

from src.modules.fermentation.src.api.dependencies import get_fermentation_note_repository
from src.modules.fermentation.src.api.error_handlers import handle_service_errors
from src.modules.fermentation.src.api.schemas.requests.fermentation_note_requests import (
    FermentationNoteCreateRequest,
    FermentationNoteUpdateRequest,
)
from src.modules.fermentation.src.api.schemas.responses.fermentation_note_responses import (
    FermentationNoteResponse,
)
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)
from src.modules.fermentation.src.domain.repositories.fermentation_note_repository_interface import (
    IFermentationNoteRepository,
)
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError

router = APIRouter(
    prefix="/fermentations/{fermentation_id}/notes",
    tags=["fermentation-notes"],
)


# ---------------------------------------------------------------------------
# POST  /fermentations/{fermentation_id}/notes
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a note to a fermentation",
)
@handle_service_errors
async def create_note(
    fermentation_id: int = Path(..., gt=0),
    request: FermentationNoteCreateRequest = ...,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)] = None,
) -> FermentationNoteResponse:
    dto = FermentationNoteCreate(
        note_text=request.note_text,
        created_by_user_id=current_user.user_id,
    )
    try:
        note = await repo.create(
            fermentation_id=fermentation_id,
            winery_id=current_user.winery_id,
            data=dto,
        )
    except EntityNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Fermentation {fermentation_id} not found",
        )
    return FermentationNoteResponse.from_entity(note)


# ---------------------------------------------------------------------------
# GET  /fermentations/{fermentation_id}/notes
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=List[FermentationNoteResponse],
    status_code=status.HTTP_200_OK,
    summary="List all notes for a fermentation",
)
@handle_service_errors
async def list_notes(
    fermentation_id: int = Path(..., gt=0),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)] = None,
) -> List[FermentationNoteResponse]:
    notes = await repo.list_by_fermentation(
        fermentation_id=fermentation_id,
        winery_id=current_user.winery_id,
    )
    return [FermentationNoteResponse.from_entity(n) for n in notes]


# ---------------------------------------------------------------------------
# GET  /fermentations/{fermentation_id}/notes/{note_id}
# ---------------------------------------------------------------------------

@router.get(
    "/{note_id}",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a single fermentation note",
)
@handle_service_errors
async def get_note(
    fermentation_id: int = Path(..., gt=0),
    note_id: int = Path(..., gt=0),
    current_user: Annotated[UserContext, Depends(get_current_user)] = None,
    repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)] = None,
) -> FermentationNoteResponse:
    note = await repo.get_by_id(note_id=note_id, winery_id=current_user.winery_id)
    if note is None or note.fermentation_id != fermentation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return FermentationNoteResponse.from_entity(note)


# ---------------------------------------------------------------------------
# PATCH  /fermentations/{fermentation_id}/notes/{note_id}
# ---------------------------------------------------------------------------

@router.patch(
    "/{note_id}",
    response_model=FermentationNoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a fermentation note",
)
@handle_service_errors
async def update_note(
    fermentation_id: int = Path(..., gt=0),
    note_id: int = Path(..., gt=0),
    request: FermentationNoteUpdateRequest = ...,
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)] = None,
) -> FermentationNoteResponse:
    dto = FermentationNoteUpdate(note_text=request.note_text)
    note = await repo.update(
        note_id=note_id,
        winery_id=current_user.winery_id,
        data=dto,
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
    return FermentationNoteResponse.from_entity(note)


# ---------------------------------------------------------------------------
# DELETE  /fermentations/{fermentation_id}/notes/{note_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a fermentation note (soft delete)",
)
@handle_service_errors
async def delete_note(
    fermentation_id: int = Path(..., gt=0),
    note_id: int = Path(..., gt=0),
    current_user: Annotated[UserContext, Depends(require_winemaker)] = None,
    repo: Annotated[IFermentationNoteRepository, Depends(get_fermentation_note_repository)] = None,
) -> None:
    deleted = await repo.delete(note_id=note_id, winery_id=current_user.winery_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note {note_id} not found",
        )
```

---

## Step 9 — Dependency injection

In `src/modules/fermentation/src/api/dependencies.py`, add a factory for the repository:

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.infra.db.session import get_async_session          # adjust import to your project
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)


async def get_fermentation_note_repository(
    session: AsyncSession = Depends(get_async_session),
) -> FermentationNoteRepository:
    return FermentationNoteRepository(session=session)
```

> Adapt `get_async_session` to however your project exposes a per-request `AsyncSession`.

---

## Step 10 — Register the router in `main.py`

```python
# src/modules/fermentation/src/main.py  (additions)

from src.modules.fermentation.src.api.routers.fermentation_note_router import (
    router as fermentation_note_router,
)

app.include_router(fermentation_note_router, prefix="/api/v1")
```

---

## Step 11 — Alembic migration

Create `alembic/versions/008_create_fermentation_notes.py`:

```python
"""Create fermentation_notes table

Revision ID: 008_create_fermentation_notes
Revises: 007_create_winemaker_actions
Create Date: 2026-04-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "008_create_fermentation_notes"
down_revision: Union[str, None] = "007_create_winemaker_actions"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fermentation_notes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fermentation_id", sa.Integer(), nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["fermentation_id"], ["fermentations.id"]),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fermentation_notes_fermentation_id", "fermentation_notes", ["fermentation_id"])
    op.create_index("ix_fermentation_notes_created_by_user_id", "fermentation_notes", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_fermentation_notes_created_by_user_id", table_name="fermentation_notes")
    op.drop_index("ix_fermentation_notes_fermentation_id", table_name="fermentation_notes")
    op.drop_table("fermentation_notes")
```

Apply it:

```bash
alembic upgrade head
```

---

## Step 12 — Tests

### Unit test — DTO validation
`tests/unit/domain/test_fermentation_note_dtos.py`:

```python
import pytest
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import (
    FermentationNoteCreate,
    FermentationNoteUpdate,
)


def test_create_dto_strips_whitespace():
    dto = FermentationNoteCreate(note_text="  hello  ", created_by_user_id=1)
    assert dto.note_text == "hello"


def test_create_dto_rejects_blank_text():
    with pytest.raises(ValueError, match="note_text"):
        FermentationNoteCreate(note_text="   ", created_by_user_id=1)


def test_create_dto_rejects_invalid_user_id():
    with pytest.raises(ValueError):
        FermentationNoteCreate(note_text="ok", created_by_user_id=0)


def test_update_dto_has_updates():
    assert FermentationNoteUpdate(note_text="new").has_updates() is True
    assert FermentationNoteUpdate().has_updates() is False
```

### Unit test — repository (mock session)
`tests/unit/repository_component/test_fermentation_note_repository.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import FermentationNoteCreate
from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
from src.modules.fermentation.src.repository_component.errors import EntityNotFoundError
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.__aenter__ = AsyncMock(return_value=session)
    session.__aexit__ = AsyncMock(return_value=False)
    return session


@pytest.fixture
def repo(mock_session):
    r = FermentationNoteRepository.__new__(FermentationNoteRepository)
    r.get_session = AsyncMock(return_value=mock_session)
    return r


@pytest.mark.asyncio
async def test_create_raises_when_fermentation_not_found(repo, mock_session):
    mock_session.scalar = AsyncMock(return_value=None)  # no fermentation found
    with pytest.raises(EntityNotFoundError):
        await repo.create(
            fermentation_id=99,
            winery_id=1,
            data=FermentationNoteCreate(note_text="test", created_by_user_id=1),
        )


@pytest.mark.asyncio
async def test_delete_returns_false_when_not_found(repo, mock_session):
    mock_session.scalar = AsyncMock(return_value=None)
    result = await repo.delete(note_id=99, winery_id=1)
    assert result is False
```

### Integration test sketch

```python
# tests/integration/repository_component/test_fermentation_note_repository_integration.py

import pytest
from src.modules.fermentation.src.domain.dtos.fermentation_note_dtos import FermentationNoteCreate
from src.modules.fermentation.src.repository_component.repositories.fermentation_note_repository import (
    FermentationNoteRepository,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_create_and_list(db_session, seed_fermentation):
    """
    seed_fermentation: pytest fixture that inserts a Fermentation row
    and returns (fermentation_id, winery_id).
    """
    fermentation_id, winery_id = seed_fermentation
    repo = FermentationNoteRepository(session=db_session)

    dto = FermentationNoteCreate(note_text="Brix dropped nicely", created_by_user_id=1)
    note = await repo.create(fermentation_id, winery_id, dto)

    assert note.id is not None
    assert note.note_text == "Brix dropped nicely"
    assert note.created_at is not None

    notes = await repo.list_by_fermentation(fermentation_id, winery_id)
    assert len(notes) == 1
    assert notes[0].id == note.id
```

---

## Step 13 — API contract summary

| Method | URL | Auth role | Description |
|---|---|---|---|
| `POST` | `/api/v1/fermentations/{id}/notes` | WINEMAKER | Create a note |
| `GET` | `/api/v1/fermentations/{id}/notes` | any authenticated | List notes (newest first) |
| `GET` | `/api/v1/fermentations/{id}/notes/{note_id}` | any authenticated | Get one note |
| `PATCH` | `/api/v1/fermentations/{id}/notes/{note_id}` | WINEMAKER | Edit note text |
| `DELETE` | `/api/v1/fermentations/{id}/notes/{note_id}` | WINEMAKER | Soft-delete a note |

**Example `POST` request body:**
```json
{ "note_text": "Reducing temperature — fermentation running hot." }
```

**Example response:**
```json
{
  "id": 42,
  "fermentation_id": 7,
  "created_by_user_id": 3,
  "note_text": "Reducing temperature — fermentation running hot.",
  "created_at": "2026-04-18T09:15:00",
  "updated_at": "2026-04-18T09:15:00"
}
```

---

## Security & design notes

| Concern | Approach |
|---|---|
| **Multi-tenancy** | Every query JOINs through `Fermentation.winery_id`. A winemaker from Winery A can never read or modify notes belonging to Winery B. |
| **Author spoofing** | `created_by_user_id` is taken from the validated JWT (`current_user.user_id`), not from the request body. |
| **Timestamp** | `created_at` is set by the database/ORM (`default=datetime.utcnow`), not by the client. |
| **Soft delete** | Physical deletes are never issued; `is_deleted=True` hides the record without losing audit history. |
| **Authorisation** | Only WINEMAKER (or ADMIN) roles can create, update, or delete notes; read is available to any authenticated user in the same winery. |

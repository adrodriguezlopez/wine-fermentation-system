"""
Request / Response schemas for FermentationNote API endpoints.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# Request schemas
# =============================================================================

class NoteCreateRequest(BaseModel):
    """Payload for POST /fermentations/{fermentation_id}/notes."""

    note_text: str = Field(
        ..., min_length=1, max_length=10000,
        description="Free-text observation from the winemaker"
    )
    action_taken: str = Field(
        ..., min_length=1, max_length=255,
        description="Short description of the action taken"
    )


class NoteUpdateRequest(BaseModel):
    """Payload for PATCH /notes/{note_id}. All fields optional."""

    note_text: Optional[str] = Field(
        None, min_length=1, max_length=10000,
        description="Updated note text"
    )
    action_taken: Optional[str] = Field(
        None, min_length=1, max_length=255,
        description="Updated action description"
    )


# =============================================================================
# Response schemas
# =============================================================================

class NoteResponse(BaseModel):
    """Single FermentationNote serialised for API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    fermentation_id: int
    note_text: str
    action_taken: str
    created_by_user_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime


class NoteListResponse(BaseModel):
    """List of FermentationNote entries."""

    items: List[NoteResponse]

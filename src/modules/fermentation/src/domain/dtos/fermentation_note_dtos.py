"""
Fermentation Note Data Transfer Objects.

DTOs for fermentation note creation and update operations.
Following ADR-009: Phase 3 - Fermentation Note Repository Implementation.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class FermentationNoteCreate:
    """
    DTO for creating a new fermentation note.
    
    Attributes:
        note_text: Text content of the note (required)
        action_taken: Action taken by the user (required, max 255 chars)
        created_by_user_id: ID of the user creating the note (required)
    """
    note_text: str
    action_taken: str
    created_by_user_id: int

    def __post_init__(self):
        """Validate fermentation note creation data."""
        if not self.note_text or not self.note_text.strip():
            raise ValueError("Note text is required")
        
        if not self.action_taken or not self.action_taken.strip():
            raise ValueError("Action taken is required")
        
        if len(self.action_taken) > 255:
            raise ValueError("Action taken cannot exceed 255 characters")
        
        if not isinstance(self.created_by_user_id, int) or self.created_by_user_id <= 0:
            raise ValueError("created_by_user_id must be a positive integer")
        
        # Strip whitespace
        self.note_text = self.note_text.strip()
        self.action_taken = self.action_taken.strip()


@dataclass
class FermentationNoteUpdate:
    """
    DTO for updating fermentation note information.
    
    All fields are optional for partial updates.
    
    Attributes:
        note_text: Updated text content of the note (optional)
        action_taken: Updated action taken (optional, max 255 chars)
    """
    note_text: Optional[str] = None
    action_taken: Optional[str] = None

    def __post_init__(self):
        """Validate fermentation note update data."""
        if self.note_text is not None:
            if not self.note_text.strip():
                raise ValueError("Note text cannot be empty")
            self.note_text = self.note_text.strip()
        
        if self.action_taken is not None:
            if not self.action_taken.strip():
                raise ValueError("Action taken cannot be empty")
            
            if len(self.action_taken) > 255:
                raise ValueError("Action taken cannot exceed 255 characters")
            
            self.action_taken = self.action_taken.strip()

    def has_updates(self) -> bool:
        """
        Check if this DTO contains any updates.
        
        Returns:
            bool: True if at least one field is set
        """
        return self.note_text is not None or self.action_taken is not None

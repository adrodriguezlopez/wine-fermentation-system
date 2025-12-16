"""
Domain Data Transfer Objects.

DTOs are simple data structures used to transfer data between layers.
These are framework-agnostic (no Pydantic, no ORM) - pure Python dataclasses.
"""

from .fermentation_dtos import (
    FermentationCreate,
    FermentationUpdate,
    FermentationWithBlendCreate,
    LotSourceData
)
from .sample_dtos import SampleCreate
from .fermentation_note_dtos import FermentationNoteCreate, FermentationNoteUpdate

__all__ = [
    "FermentationCreate",
    "FermentationUpdate",
    "FermentationWithBlendCreate",
    "LotSourceData",
    "SampleCreate",
    "FermentationNoteCreate",
    "FermentationNoteUpdate",
]

"""
Domain Data Transfer Objects.

DTOs are simple data structures used to transfer data between layers.
These are framework-agnostic (no Pydantic, no ORM) - pure Python dataclasses.
"""

from .fermentation_dtos import FermentationCreate
from .sample_dtos import SampleCreate

__all__ = [
    "FermentationCreate",
    "SampleCreate",
]

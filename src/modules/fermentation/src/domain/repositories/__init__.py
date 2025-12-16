"""
Domain repository interfaces
--------------------------
Core repository interfaces that define the persistence contracts for domain entities.
"""

from .fermentation_repository_interface import IFermentationRepository
from .sample_repository_interface import ISampleRepository
from .fermentation_note_repository_interface import IFermentationNoteRepository

__all__ = ['IFermentationRepository', 'ISampleRepository', 'IFermentationNoteRepository']

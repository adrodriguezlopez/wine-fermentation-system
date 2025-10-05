"""
Repository implementations for the fermentation module.
Concrete classes that implement domain repository interfaces.

Following ADR-003: Separated FermentationRepository and SampleRepository.
"""

from .fermentation_repository import FermentationRepository
from .sample_repository import SampleRepository

__all__ = ['FermentationRepository', 'SampleRepository']
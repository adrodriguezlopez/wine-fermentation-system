"""
Domain repository interfaces
--------------------------
Core repository interfaces that define the persistence contracts for domain entities.
"""

from .fermentation_repository_interface import IFermentationRepository
from .sample_repository_interface import ISampleRepository

__all__ = ['IFermentationRepository', 'ISampleRepository']

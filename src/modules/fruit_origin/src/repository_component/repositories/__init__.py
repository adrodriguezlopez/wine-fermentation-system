"""
Repository implementations for the fruit_origin module.
Concrete classes that implement domain repository interfaces.

Following ADR-009: Missing Repositories Implementation.
"""

from .harvest_lot_repository import HarvestLotRepository

__all__ = ['HarvestLotRepository']

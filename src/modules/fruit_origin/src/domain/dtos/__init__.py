"""
Fruit Origin Module DTOs.

Data Transfer Objects for fruit origin entities.
Pure Python dataclasses with no framework dependencies.
"""

from .harvest_lot_dtos import (
    HarvestLotCreate,
    HarvestLotUpdate,
    HarvestLotSummary
)

__all__ = [
    'HarvestLotCreate',
    'HarvestLotUpdate',
    'HarvestLotSummary',
]

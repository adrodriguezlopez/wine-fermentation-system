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
from .vineyard_dtos import (
    VineyardCreate,
    VineyardUpdate,
)
from .vineyard_block_dtos import (
    VineyardBlockCreate,
    VineyardBlockUpdate,
)

__all__ = [
    'HarvestLotCreate',
    'HarvestLotUpdate',
    'HarvestLotSummary',
    'VineyardCreate',
    'VineyardUpdate',
    'VineyardBlockCreate',
    'VineyardBlockUpdate',
]

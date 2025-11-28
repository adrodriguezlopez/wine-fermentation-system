"""
Repository implementations for the fruit_origin module.
Concrete classes that implement domain repository interfaces.

Following ADR-009: Missing Repositories Implementation.
"""

from .harvest_lot_repository import HarvestLotRepository
from .vineyard_repository import VineyardRepository
from .vineyard_block_repository import VineyardBlockRepository

__all__ = [
    'HarvestLotRepository',
    'VineyardRepository',
    'VineyardBlockRepository',
]

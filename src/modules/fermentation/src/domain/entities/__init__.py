"""
Domain Entities
-------------
Core business entities that represent the fundamental data structures
of the fermentation domain.

Path configuration is handled at module level.

NOTE: This __init__.py intentionally does NOT import entities to avoid
SQLAlchemy registry conflicts during pytest discovery.
Import entities directly from their modules instead:
    from src.modules.fermentation.src.domain.entities.user import User
"""

__all__ = [
    'BaseEntity',
    'Fermentation', 
    'FermentationNote', 
    'FermentationLotSource', 
    'User', 
    'BaseSample', 
    'SugarSample', 
    'DensitySample', 
    'CelsiusTemperatureSample'
]

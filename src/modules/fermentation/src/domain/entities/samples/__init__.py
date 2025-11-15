"""
Sample Entities
-------------
Different types of measurements that can be taken during fermentation.

NOTE: This __init__.py intentionally does NOT import entities to avoid
SQLAlchemy registry conflicts during pytest discovery.
Import sample entities directly from their modules.
"""

__all__ = [
    'BaseSample',
    'SugarSample',
    'DensitySample',
    'CelsiusTemperatureSample'
]

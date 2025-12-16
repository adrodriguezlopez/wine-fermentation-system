"""
EntityFactory - Creates mock entities with realistic test data

Provides a factory for creating domain entities with sensible defaults
and easy customization for unit tests.

Usage:
    # Simple creation with defaults
    fermentation = EntityFactory.create(Fermentation)
    
    # With custom values
    fermentation = EntityFactory.create(
        Fermentation,
        id=UUID("..."),
        vintage_year=2023
    )
    
    # Batch creation
    fermentations = EntityFactory.create_batch(Fermentation, count=5)
"""

from typing import Type, TypeVar, Any, Dict, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, date
from unittest.mock import MagicMock
from decimal import Decimal

T = TypeVar('T')


class EntityDefaults:
    """
    Registry of default values for entity types.
    
    Provides sensible defaults for common entity fields to reduce
    test boilerplate while maintaining realistic test data.
    """
    
    # Common defaults for all entities
    COMMON = {
        'id': lambda: uuid4(),
        'created_at': lambda: datetime.now(),
        'updated_at': lambda: datetime.now(),
        'created_by': lambda: UUID('00000000-0000-0000-0000-000000000001'),
        'updated_by': lambda: UUID('00000000-0000-0000-0000-000000000001'),
    }
    
    # Entity-specific defaults
    ENTITY_DEFAULTS: Dict[str, Dict[str, Any]] = {
        'Fermentation': {
            'name': lambda: f'Test Fermentation {uuid4().hex[:8]}',
            'vintage_year': lambda: 2024,
            'lot_number': lambda: f'LOT-{uuid4().hex[:8].upper()}',
            'start_date': lambda: date(2024, 1, 1),
            'end_date': None,
            'is_active': True,
        },
        'FermentationNote': {
            'note': lambda: 'Test note',
            'note_type': lambda: 'OBSERVATION',
            'recorded_at': lambda: datetime.now(),
        },
        'Sample': {
            'value': lambda: Decimal('1.050'),
            'recorded_at': lambda: datetime.now(),
        },
        'DensitySample': {
            'value': lambda: Decimal('1.050'),
            'recorded_at': lambda: datetime.now(),
        },
        'TemperatureSample': {
            'value': lambda: Decimal('20.0'),
            'recorded_at': lambda: datetime.now(),
        },
        'SugarSample': {
            'value': lambda: Decimal('200.0'),
            'recorded_at': lambda: datetime.now(),
        },
        'Winery': {
            'name': lambda: f'Test Winery {uuid4().hex[:8]}',
            'code': lambda: f'WIN-{uuid4().hex[:6].upper()}',
        },
        'FruitOrigin': {
            'name': lambda: f'Test Origin {uuid4().hex[:8]}',
            'country': lambda: 'Test Country',
        },
    }
    
    @classmethod
    def get_defaults(cls, entity_type: str) -> Dict[str, Any]:
        """
        Get default values for an entity type.
        
        Args:
            entity_type: Name of the entity class
            
        Returns:
            Dictionary of default field values
        """
        defaults = cls.COMMON.copy()
        
        if entity_type in cls.ENTITY_DEFAULTS:
            defaults.update(cls.ENTITY_DEFAULTS[entity_type])
        
        return defaults
    
    @classmethod
    def register(cls, entity_type: str, defaults: Dict[str, Any]) -> None:
        """
        Register custom defaults for an entity type.
        
        Args:
            entity_type: Name of the entity class
            defaults: Dictionary of default field values
        """
        if entity_type not in cls.ENTITY_DEFAULTS:
            cls.ENTITY_DEFAULTS[entity_type] = {}
        
        cls.ENTITY_DEFAULTS[entity_type].update(defaults)


class EntityFactory:
    """
    Factory for creating mock entities with realistic test data.
    
    Automatically generates sensible defaults for common fields while
    allowing easy customization of specific values.
    """
    
    @staticmethod
    def create(entity_class: Type[T], **overrides) -> T:
        """
        Create a mock entity with default values and overrides.
        
        Args:
            entity_class: The entity class to create
            **overrides: Field values to override defaults
            
        Returns:
            Mock entity instance with configured values
            
        Examples:
            # With defaults
            fermentation = EntityFactory.create(Fermentation)
            
            # With custom values
            fermentation = EntityFactory.create(
                Fermentation,
                vintage_year=2023,
                name="My Fermentation"
            )
        """
        # Create mock entity
        entity = MagicMock(spec=entity_class)
        
        # Get entity type name
        entity_type = entity_class.__name__
        
        # Get defaults for this entity type
        defaults = EntityDefaults.get_defaults(entity_type)
        
        # Apply defaults
        for field, value_or_callable in defaults.items():
            if field not in overrides:
                # Call if it's a lambda/callable, otherwise use value directly
                value = value_or_callable() if callable(value_or_callable) else value_or_callable
                setattr(entity, field, value)
        
        # Apply overrides
        for field, value in overrides.items():
            setattr(entity, field, value)
        
        # Set __class__ for isinstance checks
        type(entity).__name__ = entity_type
        
        return entity
    
    @staticmethod
    def create_batch(
        entity_class: Type[T],
        count: int,
        **common_overrides
    ) -> List[T]:
        """
        Create multiple entities with the same overrides.
        
        Args:
            entity_class: The entity class to create
            count: Number of entities to create
            **common_overrides: Overrides applied to all entities
            
        Returns:
            List of mock entities
            
        Example:
            fermentations = EntityFactory.create_batch(
                Fermentation,
                count=5,
                vintage_year=2023
            )
        """
        return [
            EntityFactory.create(entity_class, **common_overrides)
            for _ in range(count)
        ]
    
    @staticmethod
    def create_sequence(
        entity_class: Type[T],
        count: int,
        sequence_field: str,
        start: int = 1,
        **common_overrides
    ) -> List[T]:
        """
        Create entities with a sequential field value.
        
        Args:
            entity_class: The entity class to create
            count: Number of entities to create
            sequence_field: Field to increment sequentially
            start: Starting value for sequence
            **common_overrides: Overrides applied to all entities
            
        Returns:
            List of mock entities with sequential field
            
        Example:
            fermentations = EntityFactory.create_sequence(
                Fermentation,
                count=5,
                sequence_field='vintage_year',
                start=2020
            )
        """
        entities = []
        for i in range(count):
            overrides = common_overrides.copy()
            overrides[sequence_field] = start + i
            entities.append(EntityFactory.create(entity_class, **overrides))
        
        return entities


def create_mock_entity(entity_class: Type[T], **kwargs) -> T:
    """
    Convenience function for creating a single mock entity.
    
    Args:
        entity_class: The entity class to create
        **kwargs: Field values to override defaults
        
    Returns:
        Mock entity instance
        
    Example:
        fermentation = create_mock_entity(Fermentation, vintage_year=2023)
    """
    return EntityFactory.create(entity_class, **kwargs)


def create_mock_entities(entity_class: Type[T], count: int, **kwargs) -> List[T]:
    """
    Convenience function for creating multiple mock entities.
    
    Args:
        entity_class: The entity class to create
        count: Number of entities to create
        **kwargs: Field values to override defaults
        
    Returns:
        List of mock entities
        
    Example:
        fermentations = create_mock_entities(Fermentation, 5, vintage_year=2023)
    """
    return EntityFactory.create_batch(entity_class, count, **kwargs)

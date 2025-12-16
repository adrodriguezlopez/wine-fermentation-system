"""
Test entity builder utilities.

Provides consistent, reusable patterns for creating test entities.
"""

from typing import TypeVar, Type, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


T = TypeVar('T')


@dataclass
class EntityDefaults:
    """
    Default values for entity creation.
    
    Provides sensible defaults for common entity fields like
    timestamps and soft-delete flags.
    """
    
    # Common defaults
    is_deleted: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Set timestamps to current time if not provided."""
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


class EntityBuilder:
    """
    Fluent builder for test entities.
    
    Provides a clean, readable way to create test entities with
    custom field values and default values.
    
    Example:
        fermentation = (
            EntityBuilder(Fermentation)
            .with_field("winery_id", test_winery.id)
            .with_field("vintage_year", 2024)
            .with_field("yeast_strain", "EC-1118")
            .with_defaults(EntityDefaults())
            .build()
        )
    """
    
    def __init__(self, entity_class: Type[T]):
        """
        Initialize builder with entity class.
        
        Args:
            entity_class: Entity class to instantiate
        """
        self.entity_class = entity_class
        self.fields = {}
    
    def with_field(self, name: str, value: Any) -> 'EntityBuilder':
        """
        Set a field value.
        
        Args:
            name: Field name
            value: Field value
        
        Returns:
            Self for method chaining
        """
        self.fields[name] = value
        return self
    
    def with_fields(self, **kwargs) -> 'EntityBuilder':
        """
        Set multiple fields at once.
        
        Args:
            **kwargs: Field name-value pairs
        
        Returns:
            Self for method chaining
        """
        self.fields.update(kwargs)
        return self
    
    def with_defaults(self, defaults: EntityDefaults) -> 'EntityBuilder':
        """
        Apply default values.
        
        Only sets fields that haven't been explicitly set yet.
        
        Args:
            defaults: EntityDefaults instance with default values
        
        Returns:
            Self for method chaining
        """
        for key, value in defaults.__dict__.items():
            if key not in self.fields and value is not None:
                self.fields[key] = value
        return self
    
    def with_unique_code(self, prefix: str = "TEST") -> 'EntityBuilder':
        """
        Generate unique code field.
        
        Creates a code like "TEST-A1B2C3D4".
        
        Args:
            prefix: Prefix for the code
        
        Returns:
            Self for method chaining
        """
        self.fields['code'] = f"{prefix}-{uuid4().hex[:8].upper()}"
        return self
    
    def build(self) -> T:
        """
        Create the entity instance.
        
        Returns:
            Entity instance with all configured fields
        """
        return self.entity_class(**self.fields)


async def create_test_entity(
    db_session,
    entity_class: Type[T],
    **kwargs
) -> T:
    """
    Create and persist a test entity.
    
    This is a convenience function for the common pattern of creating
    an entity, adding it to the session, and flushing to assign an ID.
    
    Args:
        db_session: Test database session
        entity_class: Entity class to instantiate
        **kwargs: Entity field values
    
    Returns:
        Created and persisted entity with ID assigned
    
    Example:
        fermentation = await create_test_entity(
            db_session,
            Fermentation,
            winery_id=winery.id,
            vintage_year=2024,
            yeast_strain="EC-1118"
        )
        
        assert fermentation.id is not None  # ID assigned after flush
    """
    entity = entity_class(**kwargs)
    db_session.add(entity)
    await db_session.flush()  # Assign ID without committing
    return entity

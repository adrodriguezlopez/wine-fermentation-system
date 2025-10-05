from datetime import datetime
from typing import TypeVar

from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    registry,
)

# Create a single global registry for all entities
# This prevents "Multiple classes found" errors when entities are imported multiple times
mapper_registry = registry()


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Uses a single global registry to ensure all entities are registered
    in the same namespace, preventing duplicate registration errors.
    """
    registry = mapper_registry
    __abstract__ = True


BaseType = TypeVar("BaseType", bound="BaseEntity")


class BaseEntity(Base):
    """Base entity class for all database models."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

from datetime import datetime
from typing import TypeVar

from sqlalchemy import Integer, DateTime
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""


BaseType = TypeVar("BaseType", bound="BaseEntity")


class BaseEntity(Base):
    """Base entity class for all database models."""
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

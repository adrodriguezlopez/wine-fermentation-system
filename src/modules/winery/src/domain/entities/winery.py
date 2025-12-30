"""
Winery entity.

Represents a winery organization that owns fermentations, users, and harvest lots.
"""

from typing import Optional
from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.shared.infra.orm.base_entity import BaseEntity


class Winery(BaseEntity):
    """
    Winery entity representing a wine production facility.
    
    A winery is the top-level organization that owns:
    - Users (winemakers and staff)
    - Fermentations
    - Harvest lots
    
    Attributes:
        code: Unique identifier code for the winery (e.g., "BODEGA-001")
        name: Name of the winery
        location: Geographic location where the winery is situated
        notes: Additional notes about the winery
    """
    __tablename__ = "wineries"
    __table_args__ = (
        UniqueConstraint("name", name="uq_wineries__name"),
        UniqueConstraint("code", name="uq_wineries__code"),
        {"extend_existing": True}
    )
    
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    def __repr__(self) -> str:
        return f"<Winery(id={self.id}, code='{self.code}', name='{self.name}', location='{self.location}', is_deleted={self.is_deleted})>"

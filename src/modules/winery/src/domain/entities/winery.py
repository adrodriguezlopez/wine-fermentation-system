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
        name: Name of the winery
        region: Geographic region where the winery is located
    """
    __tablename__ = "wineries"
    __table_args__ = (
        UniqueConstraint("name", name="uq_wineries__name"),
        {"extend_existing": True}
    )
    
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    def __repr__(self) -> str:
        return f"<Winery(id={self.id}, name='{self.name}', region='{self.region}', is_deleted={self.is_deleted})>"

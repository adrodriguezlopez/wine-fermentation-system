from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, ForeignKey
from typing import List, Optional
from domain.entities.base_entity import BaseEntity

class Vineyard(BaseEntity):
    __tablename__ = "vineyards"
    __table_args__ = (
        # Unique code per winery
        {"sqlite_autoincrement": True},
    )

    winery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wineries.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    blocks: Mapped[List["VineyardBlock"]] = relationship("VineyardBlock", back_populates="vineyard", cascade="all, delete-orphan")

    __table_args__ = (
        # Unique code per winery
        # (enforced at DB level)
        # Note: SQLAlchemy 2.0 style
        # UniqueConstraint is imported from sqlalchemy
        # but not shown here for brevity
        # Add it in the migration or model as needed
        # e.g., UniqueConstraint('code', 'winery_id', name='uq_vineyards__code__winery_id')
    )

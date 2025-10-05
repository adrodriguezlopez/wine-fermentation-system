from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, ForeignKey, UniqueConstraint
from typing import List, Optional
from src.shared.infra.orm.base_entity import BaseEntity

class Vineyard(BaseEntity):
    __tablename__ = "vineyards"
    __table_args__ = (
        # Unique code per winery (ADR-001 constraint)
        UniqueConstraint('code', 'winery_id', name='uq_vineyards__code__winery_id'),
        {"sqlite_autoincrement": True, "extend_existing": True},
    )

    winery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wineries.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    blocks: Mapped[List["VineyardBlock"]] = relationship("VineyardBlock", back_populates="vineyard", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vineyard(id={self.id}, code='{self.code}', name='{self.name}', winery_id={self.winery_id})>"

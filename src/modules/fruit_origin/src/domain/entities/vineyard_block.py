from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, ForeignKey, Numeric, DECIMAL, Boolean, UniqueConstraint
from typing import List, Optional
from src.shared.infra.orm.base_entity import BaseEntity

class VineyardBlock(BaseEntity):
    __tablename__ = "vineyard_blocks"
    __table_args__ = (
        # Unique code per vineyard (ADR-001 constraint)
        UniqueConstraint('code', 'vineyard_id', name='uq_vineyard_blocks__code__vineyard_id'),
        {"sqlite_autoincrement": True, "extend_existing": True},
    )

    vineyard_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vineyards.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    soil_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    slope_pct: Mapped[Optional[float]] = mapped_column(Numeric(5,2), nullable=True)
    aspect_deg: Mapped[Optional[float]] = mapped_column(Numeric(5,2), nullable=True)
    area_ha: Mapped[Optional[float]] = mapped_column(Numeric(8,3), nullable=True)
    elevation_m: Mapped[Optional[float]] = mapped_column(Numeric(8,2), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(DECIMAL(9,6), nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(DECIMAL(9,6), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    irrigation: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    organic_certified: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    vineyard: Mapped["Vineyard"] = relationship("Vineyard", back_populates="blocks")
    harvest_lots: Mapped[List["HarvestLot"]] = relationship("HarvestLot", back_populates="block", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<VineyardBlock(id={self.id}, code='{self.code}', vineyard_id={self.vineyard_id})>"

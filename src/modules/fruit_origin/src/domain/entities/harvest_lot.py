from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, BigInteger, ForeignKey, Date, Numeric, Integer, Boolean, DECIMAL, TIMESTAMP
from typing import Optional
from domain.entities.base_entity import BaseEntity

class HarvestLot(BaseEntity):
    __tablename__ = "harvest_lots"
    __table_args__ = (
        # Unique code per winery
        # Add UniqueConstraint('code', 'winery_id', name='uq_harvest_lots__code__winery_id') in migration/model
        {"sqlite_autoincrement": True},
    )

    winery_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("wineries.id"), nullable=False, index=True)
    block_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("vineyard_blocks.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    harvest_date: Mapped[Date] = mapped_column(Date, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Numeric(10,2), nullable=False)
    brix_at_harvest: Mapped[Optional[float]] = mapped_column(Numeric(5,2), nullable=True)
    brix_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    brix_measured_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., 'field', 'receival'
    grape_variety: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    clone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    rootstock: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pick_method: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., 'hand', 'machine'
    pick_start_time: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    pick_end_time: Mapped[Optional[str]] = mapped_column(TIMESTAMP, nullable=True)
    bins_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    field_temp_c: Mapped[Optional[float]] = mapped_column(Numeric(5,2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    block: Mapped["VineyardBlock"] = relationship("VineyardBlock", back_populates="harvest_lots")

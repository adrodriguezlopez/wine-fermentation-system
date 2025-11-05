from datetime import datetime
from typing import List, TYPE_CHECKING, Optional
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.shared.auth.domain.entities.user import User
    from src.modules.fermentation.src.domain.entities.fermentation_note import FermentationNote
    from src.modules.fermentation.src.domain.entities.fermentation_lot_source import FermentationLotSource
    from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class Fermentation(BaseEntity):
    __tablename__ = "fermentations"
    __table_args__ = (
        # Unique vessel code per winery (ADR-001 constraint)
        UniqueConstraint('winery_id', 'vessel_code', name='uq_fermentations__winery_id__vessel_code'),
        {
            "sqlite_autoincrement": True,
            "extend_existing": True  # Allow re-registration for testing
        },
    )

    # Core foreign keys
    fermented_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"), nullable=False, index=True)

    # Wine production details (simplified - no longer duplicate vineyard/variety info)
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False)
    yeast_strain: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Vessel identification (optional)
    vessel_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Initial measurements (renamed for clarity)
    input_mass_kg: Mapped[float] = mapped_column(Float, nullable=False)
    initial_sugar_brix: Mapped[float] = mapped_column(Float, nullable=False)
    initial_density: Mapped[float] = mapped_column(Float, nullable=False)

    # Fermentation management
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # Soft delete support
    is_deleted: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")

    # Relationships - using fully qualified paths to avoid ambiguity
    fermented_by_user: Mapped["User"] = relationship(
        "src.shared.auth.domain.entities.user.User", 
        back_populates="fermentations",
        lazy="select"
    )
    
    samples: Mapped[List["BaseSample"]] = relationship(
        "src.modules.fermentation.src.domain.entities.samples.base_sample.BaseSample",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    notes: Mapped[List["FermentationNote"]] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation_note.FermentationNote", 
        back_populates="fermentation", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Fruit origin traceability - association with HarvestLots via FermentationLotSource
    lot_sources: Mapped[List["FermentationLotSource"]] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation_lot_source.FermentationLotSource", 
        back_populates="fermentation", 
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # TODO: Add when Winery entity is implemented
    # winery: Mapped["Winery"] = relationship("Winery", back_populates="fermentations", foreign_keys=[winery_id])

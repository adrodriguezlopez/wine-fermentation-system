from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, ForeignKey, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    # NOTE: HarvestLot will be imported from fruit_origin module when needed


class FermentationLotSource(BaseEntity):
    """
    Association entity linking Fermentation to HarvestLot with usage mass.
    
    Represents the fruit composition of a fermentation, enabling blend tracking
    and traceability from wine back to specific vineyard blocks.
    
    Business Rules (enforced in domain services):
    - Sum of all mass_used_kg for a fermentation must equal fermentation.input_mass_kg
    - All harvest lots must belong to same winery as fermentation
    - HarvestLot.harvest_date must be <= Fermentation.start_date
    """
    __tablename__ = "fermentation_lot_sources"
    __table_args__ = (
        # No duplicate HarvestLot per fermentation (core constraint from ADR-001)
        UniqueConstraint(
            'fermentation_id', 'harvest_lot_id', 
            name='uq_fermentation_lot_source_fermentation_harvest'
        ),
        # CHECK constraint for positive mass (local invariant)
        CheckConstraint('mass_used_kg > 0', name='ck_fermentation_lot_source_mass_positive'),
        # Performance index for common queries (detail views, sum validations)
        Index('idx_fermentation_lot_source_fermentation', 'fermentation_id'),
        # Optional index for HarvestLot usage history queries
        Index('idx_fermentation_lot_source_harvest_lot', 'harvest_lot_id'),
        {"extend_existing": True},  # Allow re-registration for testing
    )

    # Core foreign keys (minimal required fields per ADR-001)
    fermentation_id: Mapped[int] = mapped_column(
        ForeignKey("fermentations.id"), 
        nullable=False, 
        index=True
    )
    harvest_lot_id: Mapped[int] = mapped_column(
        ForeignKey("harvest_lots.id"), 
        nullable=False, 
        index=True
    )
    
    # Mass used from this specific lot (with sufficient precision for kg decimals)
    mass_used_kg: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Optional contextual notes for this lot usage in this fermentation
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships - using fully qualified paths to avoid ambiguity
    fermentation: Mapped["Fermentation"] = relationship("src.modules.fermentation.src.domain.entities.fermentation.Fermentation", back_populates="lot_sources")
    # harvest_lot: Mapped["HarvestLot"] = relationship("HarvestLot")  # Cross-module relationship, activate when ready

    def __repr__(self) -> str:
        return (
            f"<FermentationLotSource(fermentation_id={self.fermentation_id}, "
            f"harvest_lot_id={self.harvest_lot_id}, mass_used_kg={self.mass_used_kg})>"
        )
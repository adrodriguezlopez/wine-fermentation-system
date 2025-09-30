from datetime import datetime
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity


class BaseSample(BaseEntity):
    """Base class for all sample types in fermentation monitoring."""

    __tablename__ = "samples"

    # Primary identification
    # Id is inherited from BaseEntity
    sample_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # e.g., 'glucose', 'ethanol', 'temperature'

    # Sample context
    fermentation_id: Mapped[int] = mapped_column(
        ForeignKey("fermentations.id"), nullable=False, index=True
    )
    recorded_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
    recorded_by_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )  # Soft delete flag

    # Measurement data
    value: Mapped[float] = mapped_column(nullable=False)
    units: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. g/L

    # Relationships
    fermentation = relationship("Fermentation", back_populates="samples")

    __mapper_args__ = {"polymorphic_identity": "base", "polymorphic_on": sample_type}

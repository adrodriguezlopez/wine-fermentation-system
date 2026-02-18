from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.infra.orm.base_entity import BaseEntity


class BaseSample(BaseEntity):
    """Base class for all sample types in fermentation monitoring."""

    __tablename__ = "samples"
    __table_args__ = {"extend_existing": True}  # Allow re-registration for testing
    __mapper_args__ = {
        "polymorphic_on": "sample_type",
        "polymorphic_identity": "base_sample",
    }

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
        Integer, nullable=False  # Audit: user who recorded - no FK to avoid module dependencies
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False, nullable=False
    )  # Soft delete flag
    
    # Data source tracking (ADR-029)
    data_source: Mapped[str] = mapped_column(String(20), nullable=False, default="system", server_default="system", index=True)
    imported_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    # Measurement data
    value: Mapped[float] = mapped_column(nullable=False)
    units: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g. g/L

    __mapper_args__ = {"polymorphic_identity": "base", "polymorphic_on": sample_type}

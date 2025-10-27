from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    from src.shared.auth.domain.entities.user import User


class BaseSample(BaseEntity):
    """Base class for all sample types in fermentation monitoring."""

    __tablename__ = "samples"
    __table_args__ = {"extend_existing": True}  # Allow re-registration for testing

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

    # Relationships - using fully qualified paths and Mapped types for consistency
    # Note: No back_populates for single-table inheritance to avoid mapper confusion
    fermentation: Mapped["Fermentation"] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation.Fermentation",
        viewonly=True
    )
    recorded_by_user: Mapped["User"] = relationship(
        "src.modules.fermentation.src.domain.entities.user.User",
        viewonly=True
    )

    __mapper_args__ = {"polymorphic_identity": "base", "polymorphic_on": sample_type}

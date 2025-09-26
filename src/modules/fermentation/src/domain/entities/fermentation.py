from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from domain.entities.user import User
    from domain.entities.fermentation_note import FermentationNote
    from domain.entities.samples.base_sample import BaseSample


class Fermentation(BaseEntity):
    __tablename__ = "fermentations"

    fermented_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)

    # Wine production details
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False)
    winery: Mapped[str] = mapped_column(String(100), nullable=False)
    vineyard: Mapped[str] = mapped_column(String(100), nullable=False)
    grape_variety: Mapped[str] = mapped_column(String(100), nullable=False)
    yeast_strain: Mapped[str] = mapped_column(String(100), nullable=False)

    # Initial measurements
    initial_fruit_quantity: Mapped[float] = mapped_column(Float, nullable=False)
    initial_sugar_brix: Mapped[float] = mapped_column(Float, nullable=False)
    initial_density: Mapped[float] = mapped_column(Float, nullable=False)

    # Fermentation management
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE")
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # Relationships
    fermented_by_user: Mapped["User"] = relationship("User", back_populates="fermentations", foreign_keys=[fermented_by_user_id])
    samples: Mapped[List["BaseSample"]] = relationship("BaseSample", back_populates="fermentation", cascade="all, delete-orphan")
    notes: Mapped[List["FermentationNote"]] = relationship("FermentationNote", back_populates="fermentation", cascade="all, delete-orphan")
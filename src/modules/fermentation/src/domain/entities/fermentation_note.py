from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation


class FermentationNote(BaseEntity):
    __tablename__ = "fermentation_notes"
    __table_args__ = {"extend_existing": True}  # Allow re-registration for testing

    # Foreign Key
    fermentation_id = Column(
        Integer, ForeignKey("fermentations.id"), nullable=False, index=True
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Note content
    note_text = Column(Text, nullable=False)
    action_taken = Column(String(255), nullable=False)
    
    # Soft delete flag
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="0")

    # Relationships - using fully qualified paths and Mapped types for consistency
    fermentation: Mapped["Fermentation"] = relationship(
        "src.modules.fermentation.src.domain.entities.fermentation.Fermentation", 
        back_populates="notes"
    )

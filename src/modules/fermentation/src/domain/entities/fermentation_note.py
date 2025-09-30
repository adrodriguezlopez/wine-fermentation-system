from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship

from src.shared.infra.orm.base_entity import BaseEntity


class FermentationNote(BaseEntity):
    __tablename__ = "fermentation_notes"

    # Foreign Key
    fermentation_id = Column(
        Integer, ForeignKey("fermentations.id"), nullable=False, index=True
    )
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Note content
    note_text = Column(Text, nullable=False)
    action_taken = Column(String(255), nullable=False)

    # Relationships
    fermentation = relationship("Fermentation", back_populates="notes")

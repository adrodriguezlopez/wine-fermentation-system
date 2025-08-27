from datetime import datetime
from modules.fermentation.src.service_component.models.entities.base_entity import BaseEntity
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

class BaseSample(BaseEntity):
    __tablename__ = 'samples'

    # Primary identification
    # Id is inherited from BaseEntity
    sample_type = Column(String(50), nullable=False, index=True)  # e.g., 'glucose', 'ethanol', 'temperature'

    # Sample context
    fermentation_id = Column(Integer, ForeignKey('fermentations.id'), nullable=False, index=True)
    recorded_at = Column(DateTime, nullable=False, index=True)
    recorded_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    # Measurement data
    value = Column(Float, nullable=False)
    units = Column(String(20), nullable=False)  # e.g., 'g/L', '%', '°C'

    # Relationships
    fermentation = relationship("Fermentation", back_populates="samples")

    __mapper_args__ = {
        "polymorphic_identity": "base",
        "polymorphic_on": sample_type
    }


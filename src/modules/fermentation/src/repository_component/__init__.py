"""
Repository Component for Fermentation Management
--------------------------------------------
Database access patterns for fermentation and sample data.
Handles:
- Data persistence
- Query operations
- Transaction management
- Data access optimization
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Optional

from ..service_component import FermentationStatus

Base = declarative_base()

class Fermentation(Base):
    """Fermentation database model."""
    __tablename__ = "fermentations"
    
    id = Column(Integer, primary_key=True)
    winery_id = Column(Integer, nullable=False)
    status = Column(Enum(FermentationStatus), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    samples = relationship("Sample", back_populates="fermentation")

class Sample(Base):
    """Fermentation sample measurements."""
    __tablename__ = "samples"
    
    id = Column(Integer, primary_key=True)
    fermentation_id = Column(Integer, ForeignKey("fermentations.id"))
    timestamp = Column(DateTime, nullable=False)
    glucose = Column(Float, nullable=False)
    ethanol = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    fermentation = relationship("Fermentation", back_populates="samples")

"""
FermentationProtocol Entity

Master template definition for a fermentation protocol.
Represents a varietal-specific protocol (e.g., "Pinot Noir 2021 Standard").
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity

if TYPE_CHECKING:
    from src.shared.auth.domain.entities.user import User
    from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
    from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution


class FermentationProtocol(BaseEntity):
    """
    Master protocol definition for a varietal/winery.
    
    A protocol is a reusable template that defines the fermentation steps
    for a specific wine varietal at a specific winery.
    
    Example: "R&G Pinot Noir 2021 - Standard Protocol"
    """
    
    __tablename__ = "fermentation_protocols"
    __table_args__ = (
        UniqueConstraint('winery_id', 'varietal_code', 'version', 
                        name='uq_protocols__winery_varietal_version'),
        CheckConstraint('expected_duration_days > 0'),
        CheckConstraint("color IN ('RED', 'WHITE', 'ROSÉ')"),
    )
    
    # Foreign keys
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Varietal identification
    varietal_code: Mapped[str] = mapped_column(String(10), nullable=False)  # "PN", "CH", "CS"
    varietal_name: Mapped[str] = mapped_column(String(100), nullable=False)  # "Pinot Noir"
    color: Mapped[str] = mapped_column(String(10), nullable=False, default="RED")  # RED, WHITE, ROSÉ
    
    # Protocol metadata
    protocol_name: Mapped[str] = mapped_column(String(200), nullable=False)  # "PN-2021-Standard"
    version: Mapped[str] = mapped_column(String(10), nullable=False)  # "1.0", "2.0", etc.
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Expected fermentation duration
    expected_duration_days: Mapped[int] = mapped_column(Integer, nullable=False)  # Typical fermentation length
    
    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)  # Currently in use?
    
    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, 
                                                 onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    steps: Mapped[List["ProtocolStep"]] = relationship(
        "ProtocolStep",
        back_populates="protocol",
        cascade="all, delete-orphan",
        lazy="selectin",
        foreign_keys="ProtocolStep.protocol_id"
    )
    
    executions: Mapped[List["ProtocolExecution"]] = relationship(
        "ProtocolExecution",
        back_populates="protocol",
        cascade="all, delete-orphan",
        lazy="select",
        foreign_keys="ProtocolExecution.protocol_id"
    )
    
    created_by: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        lazy="joined",
        back_populates=None
    )
    
    def __repr__(self) -> str:
        return f"<FermentationProtocol(id={self.id}, varietal={self.varietal_name}, version={self.version})>"

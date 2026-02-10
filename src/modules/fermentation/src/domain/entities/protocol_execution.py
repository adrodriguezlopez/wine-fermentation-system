"""
ProtocolExecution Entity

Tracks protocol adherence for a specific fermentation batch.
Links a Fermentation to its assigned Protocol and tracks compliance.
"""

from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Float, Integer, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity
from src.modules.fermentation.src.domain.enums.step_type import ProtocolExecutionStatus

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.fermentation import Fermentation
    from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
    from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion


class ProtocolExecution(BaseEntity):
    """
    Tracks protocol adherence for a specific fermentation.
    
    When you assign a Protocol to a Fermentation, you create a ProtocolExecution.
    This tracks which steps have been completed, which were skipped, and overall compliance.
    
    One-to-one relationship with Fermentation:
    - One fermentation can only follow one protocol
    - One protocol execution tracks one fermentation's protocol adherence
    """
    
    __tablename__ = "protocol_executions"
    __table_args__ = (
        UniqueConstraint('fermentation_id', 
                        name='uq_protocol_executions__fermentation'),
        CheckConstraint('compliance_score BETWEEN 0 AND 100'),
    )
    
    # Foreign keys
    fermentation_id: Mapped[int] = mapped_column(ForeignKey("fermentations.id"), 
                                                 nullable=False, index=True, unique=True)
    protocol_id: Mapped[int] = mapped_column(ForeignKey("fermentation_protocols.id"), 
                                             nullable=False, index=True)
    winery_id: Mapped[int] = mapped_column(ForeignKey("wineries.id"), 
                                          nullable=False, index=True)
    
    # Execution lifecycle
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)  # When fermentation started
    status: Mapped[str] = mapped_column(String(20), default="NOT_STARTED", nullable=False)  # NOT_STARTED, ACTIVE, COMPLETED, etc.
    
    # Compliance tracking
    compliance_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # 0-100%
    completed_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Count
    skipped_critical_steps: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # Count
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    fermentation: Mapped["Fermentation"] = relationship(
        "Fermentation",
        foreign_keys=[fermentation_id],
        lazy="joined"
    )
    
    protocol: Mapped["FermentationProtocol"] = relationship(
        "FermentationProtocol",
        back_populates="executions",
        foreign_keys=[protocol_id],
        lazy="joined"
    )
    
    completions: Mapped[List["StepCompletion"]] = relationship(
        "StepCompletion",
        back_populates="execution",
        cascade="all, delete-orphan",
        lazy="select",
        foreign_keys="StepCompletion.execution_id"
    )
    
    def __repr__(self) -> str:
        return f"<ProtocolExecution(fermentation_id={self.fermentation_id}, status={self.status}, compliance={self.compliance_score}%)>"

"""
StepCompletion Entity

Audit log entry for when/how a protocol step was completed.
Creates detailed record of every step action including timing, skip reasons, etc.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity
from src.modules.fermentation.src.domain.enums.step_type import SkipReason

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.protocol_execution import ProtocolExecution
    from src.modules.fermentation.src.domain.entities.protocol_step import ProtocolStep
    from src.shared.auth.domain.entities.user import User


class StepCompletion(BaseEntity):
    """
    Record of when/how a protocol step was completed (or skipped).
    
    Creates complete audit trail:
    - When was the step actually completed?
    - Was it on-time or late?
    - Was it skipped? Why?
    - Who verified it?
    
    Multiple StepCompletion records per step are allowed
    (e.g., H2S_CHECK done multiple times in a day).
    """
    
    __tablename__ = "step_completions"
    __table_args__ = (
        UniqueConstraint('execution_id', 'step_id', 'completed_at', 
                        name='uq_step_completions__execution_step_time'),
        CheckConstraint(
            "(was_skipped = true AND skip_reason IS NOT NULL) OR was_skipped = false"
        ),
    )
    
    # Foreign keys
    execution_id: Mapped[int] = mapped_column(ForeignKey("protocol_executions.id"), 
                                              nullable=False, index=True)
    step_id: Mapped[int] = mapped_column(ForeignKey("protocol_steps.id"), 
                                        nullable=False, index=True)
    verified_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Completion details
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)  # When was it done?
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Observations
    
    # Schedule compliance
    is_on_schedule: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # Within tolerance?
    days_late: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 if on-time, >0 if late
    
    # Skip/Deviation handling
    was_skipped: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    skip_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Why was it skipped?
    skip_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Detailed justification
    
    # Audit trail
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    execution: Mapped["ProtocolExecution"] = relationship(
        "ProtocolExecution",
        back_populates="completions",
        foreign_keys=[execution_id],
        lazy="joined"
    )
    
    step: Mapped["ProtocolStep"] = relationship(
        "ProtocolStep",
        back_populates="completions",
        foreign_keys=[step_id],
        lazy="joined"
    )
    
    verified_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[verified_by_user_id],
        lazy="joined"
    )
    
    def __repr__(self) -> str:
        status = "SKIPPED" if self.was_skipped else "COMPLETED"
        return f"<StepCompletion(step_id={self.step_id}, {status}, created={self.created_at.isoformat()})>"

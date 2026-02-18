"""
ProtocolStep Entity

A single step within a fermentation protocol.
Steps are ordered and define what needs to happen on each day of fermentation.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import BaseEntity
from src.modules.fermentation.src.domain.enums.step_type import StepType

if TYPE_CHECKING:
    from src.modules.fermentation.src.domain.entities.protocol_protocol import FermentationProtocol
    from src.modules.fermentation.src.domain.entities.step_completion import StepCompletion


class ProtocolStep(BaseEntity):
    """
    Single step within a fermentation protocol.
    
    Each step defines:
    - Category of work (step_type: INITIALIZATION, MONITORING, ADDITIONS, etc.)
    - Specific details (description: includes yeast type, nutrient brand, etc.)
    - When it should happen (expected_day, tolerance_hours)
    - How critical it is (is_critical, criticality_score)
    - Duration and dependencies
    
    DESIGN (Feb 10, 2026):
    - step_type = CATEGORY (e.g., INITIALIZATION) - fixed enum values
    - description = SPECIFIC STEP (e.g., "Yeast Inoculation - Red Star Premier Cuvée")
    
    This allows flexibility: new yeasts/nutrients can be added via description
    without modifying the StepType enum.
    
    Examples:
    - Type: INITIALIZATION, Description: "Cold Soak - 48 hours at 55°F"
    - Type: MONITORING, Description: "Temperature Check - Target 65-75°F"
    - Type: ADDITIONS, Description: "DAP Addition - 1/3 sugar depletion"
    - Type: CAP_MANAGEMENT, Description: "Punch Down - Manual, 3x daily"
    """
    
    __tablename__ = "protocol_steps"
    __table_args__ = (
        UniqueConstraint('protocol_id', 'step_order', 
                        name='uq_protocol_steps__protocol_order'),
        CheckConstraint('expected_day >= 0'),
        CheckConstraint('tolerance_hours >= 0'),
        CheckConstraint('duration_minutes >= 0'),
        CheckConstraint('criticality_score BETWEEN 0 AND 100'),
    )
    
    # Foreign keys
    protocol_id: Mapped[int] = mapped_column(ForeignKey("fermentation_protocols.id"), 
                                             nullable=False, index=True)
    depends_on_step_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("protocol_steps.id"), nullable=True
    )
    
    # Step sequence
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3, ...
    
    # Step definition
    step_type: Mapped[StepType] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Timing
    expected_day: Mapped[int] = mapped_column(Integer, nullable=False)  # 0 = crush day, 1 = next day, etc.
    tolerance_hours: Mapped[int] = mapped_column(Integer, default=12, nullable=False)  # ±N hours
    duration_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # How long does task take?
    
    # Criticality
    is_critical: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    criticality_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)  # 0-100
    
    # Flexibility
    can_repeat_daily: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Can do 2x/day?
    
    # Notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    protocol: Mapped["FermentationProtocol"] = relationship(
        "FermentationProtocol",
        back_populates="steps",
        foreign_keys=[protocol_id],
        lazy="joined"
    )
    
    dependency: Mapped[Optional["ProtocolStep"]] = relationship(
        "ProtocolStep",
        remote_side="[ProtocolStep.id]",
        foreign_keys=[depends_on_step_id],
        lazy="joined"
    )
    
    completions: Mapped[list["StepCompletion"]] = relationship(
        "StepCompletion",
        back_populates="step",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    def __repr__(self) -> str:
        return f"<ProtocolStep(order={self.step_order}, type={self.step_type}, day={self.expected_day})>"

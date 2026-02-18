"""
Recommendation entity - Represents a suggested action to address anomalies.

Following project pattern: Entity = ORM Model (inherits from Base).
"""
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import Base

if TYPE_CHECKING:
    from .analysis import Analysis
    from .anomaly import Anomaly
    from .recommendation_template import RecommendationTemplate


class Recommendation(Base):
    """
    Represents a recommendation for addressing detected anomalies.
    
    This entity follows the project pattern where Entity = ORM Model,
    combining domain logic with SQLAlchemy persistence mapping.
    """
    __tablename__ = "recommendation"
    __table_args__ = (
        Index("ix_recommendation_analysis_id", "analysis_id"),
        Index("ix_recommendation_anomaly_id", "anomaly_id"),
        Index("ix_recommendation_template_id", "recommendation_template_id"),
        Index("ix_recommendation_priority", "priority"),
        Index("ix_recommendation_is_applied", "is_applied"),
        {"extend_existing": True}
    )
    
    # Primary key
    id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    analysis_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("analysis.id", ondelete="CASCADE"),
        nullable=False
    )
    anomaly_id: Mapped[Optional[PGUUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("anomaly.id", ondelete="SET NULL"),
        nullable=True
    )
    recommendation_template_id: Mapped[PGUUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("recommendation_template.id"),
        nullable=False
    )
    
    # Recommendation details
    recommendation_text: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    supporting_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Application tracking
    is_applied: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    applied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="recommendations")
    anomaly: Mapped[Optional["Anomaly"]] = relationship(
        "Anomaly",
        back_populates="recommendations",
        foreign_keys=[anomaly_id]
    )
    template: Mapped["RecommendationTemplate"] = relationship("RecommendationTemplate")
    
    def __init__(self, **kwargs):
        """Initialize with validation."""
        super().__init__(**kwargs)
        # Validate after initialization
        if hasattr(self, 'confidence') and not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if hasattr(self, 'priority') and self.priority < 1:
            raise ValueError(f"Priority must be >= 1, got {self.priority}")
        if hasattr(self, 'supporting_evidence_count') and self.supporting_evidence_count < 0:
            raise ValueError(f"Supporting evidence count cannot be negative")
    
    def apply(self) -> None:
        """
        Mark this recommendation as applied.
        
        Raises:
            ValueError: If recommendation is already applied
        """
        if self.is_applied:
            raise ValueError("Recommendation is already applied")
        self.is_applied = True
        self.applied_at = datetime.now(timezone.utc)
    
    @property
    def urgency(self) -> str:
        """
        Get urgency level based on priority.
        
        Returns:
            "immediate", "soon", or "routine"
        """
        if self.priority == 1:
            return "immediate"
        elif self.priority <= 3:
            return "soon"
        else:
            return "routine"

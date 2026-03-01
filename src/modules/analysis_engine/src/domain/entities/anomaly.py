"""
Anomaly entity - Represents a detected problem in fermentation.

Following project pattern: Entity = ORM Model (inherits from Base).
"""
from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import Base
from ..enums.anomaly_type import AnomalyType
from ..enums.severity_level import SeverityLevel

if TYPE_CHECKING:
    from .analysis import Analysis
    from .recommendation import Recommendation


class Anomaly(Base):
    """
    Represents a detected anomaly in a fermentation analysis.
    
    This entity follows the project pattern where Entity = ORM Model,
    combining domain logic with SQLAlchemy persistence mapping.
    """
    __tablename__ = "anomaly"
    __table_args__ = (
        Index("ix_anomaly_analysis_id", "analysis_id"),
        Index("ix_anomaly_sample_id", "sample_id"),
        Index("ix_anomaly_type", "anomaly_type"),
        Index("ix_anomaly_severity", "severity"),
        Index("ix_anomaly_is_resolved", "is_resolved"),
        Index("ix_anomaly_detected_at", "detected_at"),
        Index("ix_anomaly_type_severity", "anomaly_type", "severity"),
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
    sample_id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    
    # Anomaly details
    anomaly_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Statistical details (stored as JSONB)
    deviation_score: Mapped[dict] = mapped_column(JSONB, nullable=False)
    
    # Resolution tracking
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship("Analysis", back_populates="anomalies")
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="anomaly",
        foreign_keys="Recommendation.anomaly_id"
    )

    def __init__(
        self,
        analysis_id=None,
        anomaly_type=None,
        severity=None,
        sample_id=None,
        deviation_score=None,
        description=None,
        **kwargs,
    ):
        """
        Initialize Anomaly entity with Python-level defaults.

        Accepts the six main fields as positional *or* keyword arguments for
        compatibility with tests. SQLAlchemy ``default`` values for ``id`` and
        ``detected_at`` are applied immediately so unit tests work without a DB.
        """
        from src.modules.analysis_engine.src.domain.value_objects.deviation_score import DeviationScore

        # Merge positional args into kwargs
        if analysis_id is not None:
            kwargs["analysis_id"] = analysis_id
        if anomaly_type is not None:
            # Accept enum or string
            kwargs["anomaly_type"] = anomaly_type.value if hasattr(anomaly_type, "value") else anomaly_type
        if severity is not None:
            kwargs["severity"] = severity.value if hasattr(severity, "value") else severity
        if sample_id is not None:
            kwargs["sample_id"] = sample_id
        if description is not None:
            kwargs["description"] = description

        # Apply Python-level defaults
        if "id" not in kwargs:
            kwargs["id"] = uuid4()
        if "detected_at" not in kwargs:
            kwargs["detected_at"] = datetime.now(timezone.utc)
        if "is_resolved" not in kwargs:
            kwargs["is_resolved"] = False

        # Serialize DeviationScore to dict for JSONB storage
        ds = deviation_score if deviation_score is not None else kwargs.pop("deviation_score", None)
        if isinstance(ds, DeviationScore):
            kwargs["deviation_score"] = ds.to_dict()
        elif ds is not None:
            kwargs["deviation_score"] = ds
        elif "deviation_score" not in kwargs:
            kwargs["deviation_score"] = {}

        super().__init__(**kwargs)

    def resolve(self) -> None:
        """
        Mark this anomaly as resolved.
        
        Raises:
            ValueError: If anomaly is already resolved
        """
        if self.is_resolved:
            raise ValueError("Anomaly is already resolved")
        self.is_resolved = True
        self.resolved_at = datetime.now(timezone.utc)
    
    @property
    def priority(self) -> int:
        """Get priority based on anomaly type and severity."""
        anomaly_type_enum = AnomalyType(self.anomaly_type)
        return anomaly_type_enum.priority

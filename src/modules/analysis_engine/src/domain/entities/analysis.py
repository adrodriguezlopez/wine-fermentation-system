"""
Analysis entity - Aggregate Root for fermentation analysis.

Represents a complete analysis of a fermentation, including detected anomalies
and generated recommendations.

Following project pattern: Entity = ORM Model (inherits from BaseEntity).
"""
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import Base
from ..enums.analysis_status import AnalysisStatus

if TYPE_CHECKING:
    from .anomaly import Anomaly
    from .recommendation import Recommendation


class Analysis(Base):
    """
    Aggregate Root for fermentation analysis.
    
    Coordinates the analysis process, manages anomalies and recommendations,
    and tracks analysis status.
    
    This entity follows the project pattern where Entity = ORM Model,
    combining domain logic with SQLAlchemy persistence mapping.
    """
    __tablename__ = "analysis"
    __table_args__ = (
        Index("ix_analysis_winery_id", "winery_id"),
        Index("ix_analysis_fermentation_id", "fermentation_id"),
        Index("ix_analysis_status", "status"),
        Index("ix_analysis_analyzed_at", "analyzed_at"),
        Index("ix_analysis_winery_fermentation", "winery_id", "fermentation_id"),
        Index("ix_analysis_winery_status", "winery_id", "status"),
        {"extend_existing": True}
    )
    
    # Primary key
    id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign keys
    fermentation_id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    winery_id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    
    # Status and timing
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=AnalysisStatus.PENDING.value)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(timezone.utc)
    )
    
    # Comparison and confidence (stored as JSONB)
    comparison_result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    confidence_level: Mapped[dict] = mapped_column(JSONB, nullable=False)
    historical_samples_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # Relationships
    anomalies: Mapped[List["Anomaly"]] = relationship(
        "Anomaly",
        back_populates="analysis",
        lazy="selectin",
        cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        "Recommendation",
        back_populates="analysis",
        lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __init__(
        self,
        fermentation_id=None,
        winery_id=None,
        comparison_result=None,
        confidence_level=None,
        **kwargs,
    ):
        """
        Initialize Analysis entity with Python-level defaults.

        Accepts the four main fields as positional *or* keyword arguments for
        compatibility with tests that were written before this became an ORM model.
        All remaining SQLAlchemy column kwargs are forwarded via ``**kwargs``.

        SQLAlchemy column ``default`` values only fire on DB INSERT.  This
        ``__init__`` sets them immediately so that unit tests (which never hit
        a real database) work correctly.
        """
        from src.modules.analysis_engine.src.domain.value_objects.comparison_result import ComparisonResult
        from src.modules.analysis_engine.src.domain.value_objects.confidence_level import ConfidenceLevel

        # Merge positional args into kwargs
        if fermentation_id is not None:
            kwargs["fermentation_id"] = fermentation_id
        if winery_id is not None:
            kwargs["winery_id"] = winery_id

        # Apply Python-level defaults before calling super().__init__
        if "id" not in kwargs:
            kwargs["id"] = uuid4()
        if "status" not in kwargs:
            kwargs["status"] = AnalysisStatus.PENDING.value
        if "analyzed_at" not in kwargs:
            kwargs["analyzed_at"] = datetime.now(timezone.utc)
        if "historical_samples_count" not in kwargs:
            kwargs["historical_samples_count"] = 0

        # Serialize value objects to dicts for JSONB storage
        cr = comparison_result if comparison_result is not None else kwargs.pop("comparison_result", None)
        if isinstance(cr, ComparisonResult):
            kwargs["comparison_result"] = cr.to_dict()
        elif cr is not None:
            kwargs["comparison_result"] = cr
        elif "comparison_result" not in kwargs:
            kwargs["comparison_result"] = {}

        cl = confidence_level if confidence_level is not None else kwargs.pop("confidence_level", None)
        if isinstance(cl, ConfidenceLevel):
            kwargs["confidence_level"] = cl.to_dict()
        elif cl is not None:
            kwargs["confidence_level"] = cl
        elif "confidence_level" not in kwargs:
            kwargs["confidence_level"] = {}

        super().__init__(**kwargs)

    def start(self) -> None:
        """
        Start the analysis process.
        
        Transitions status from PENDING to IN_PROGRESS.
        
        Raises:
            ValueError: If analysis is not in PENDING status
        """
        current_status = AnalysisStatus(self.status)
        if current_status != AnalysisStatus.PENDING:
            raise ValueError(
                f"Cannot start analysis in status {self.status}. "
                f"Must be in PENDING status."
            )
        self.status = AnalysisStatus.IN_PROGRESS.value
    
    def complete(self) -> None:
        """
        Complete the analysis process.
        
        Transitions status from IN_PROGRESS to COMPLETED.
        
        Raises:
            ValueError: If analysis is not in IN_PROGRESS status
        """
        current_status = AnalysisStatus(self.status)
        if current_status != AnalysisStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot complete analysis in status {self.status}. "
                f"Must be in IN_PROGRESS status."
            )
        self.status = AnalysisStatus.COMPLETED.value
    
    def fail(self, reason: str) -> None:
        """
        Mark the analysis as failed.
        
        Can be called from any status to transition to FAILED.
        
        Args:
            reason: Explanation of why the analysis failed
        """
        self.status = AnalysisStatus.FAILED.value
    
    # Methods that depend on relationships
    def add_anomaly(self, anomaly: 'Anomaly') -> None:
        """
        Add an anomaly to this analysis.

        Args:
            anomaly: The anomaly to add

        Raises:
            ValueError: If anomaly's analysis_id doesn't match this analysis
        """
        if anomaly.analysis_id != self.id:
            raise ValueError(
                f"Anomaly does not belong to this analysis. "
                f"Expected analysis_id={self.id}, got {anomaly.analysis_id}"
            )
        self.anomalies.append(anomaly)

    def add_recommendation(self, recommendation: 'Recommendation') -> None:
        """
        Add a recommendation to this analysis.

        Args:
            recommendation: The recommendation to add

        Raises:
            ValueError: If recommendation's analysis_id doesn't match this analysis
        """
        if recommendation.analysis_id != self.id:
            raise ValueError(
                f"Recommendation does not belong to this analysis. "
                f"Expected analysis_id={self.id}, got {recommendation.analysis_id}"
            )
        self.recommendations.append(recommendation)

    @property
    def has_anomalies(self) -> bool:
        """Check if analysis has detected any anomalies."""
        return len(self.anomalies) > 0

    @property
    def has_recommendations(self) -> bool:
        """Check if analysis has generated any recommendations."""
        return len(self.recommendations) > 0

    @property
    def critical_anomalies_count(self) -> int:
        """Count of critical severity anomalies."""
        from src.modules.analysis_engine.src.domain.enums.severity_level import SeverityLevel
        return sum(1 for a in self.anomalies if a.severity == SeverityLevel.CRITICAL.value)

    @property
    def is_completed(self) -> bool:
        """Check if analysis is in a final state (COMPLETED or FAILED)."""
        current_status = AnalysisStatus(self.status)
        return current_status.is_final

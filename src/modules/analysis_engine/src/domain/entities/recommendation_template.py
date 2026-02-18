"""
RecommendationTemplate entity - Template for generating recommendations.

Following project pattern: Entity = ORM Model (inherits from Base).
"""
from datetime import datetime, timezone
from typing import List, TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import String, Integer, Boolean, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.shared.infra.orm.base_entity import Base
from ..enums.anomaly_type import AnomalyType
from ..enums.recommendation_category import RecommendationCategory

if TYPE_CHECKING:
    from .recommendation import Recommendation


class RecommendationTemplate(Base):
    """
    Template for generating recommendations.
    
    This entity follows the project pattern where Entity = ORM Model,
    combining domain logic with SQLAlchemy persistence mapping.
    """
    __tablename__ = "recommendation_template"
    __table_args__ = (
        Index("ix_recommendation_template_code", "code", unique=True),
        Index("ix_recommendation_template_category", "category"),
        Index("ix_recommendation_template_is_active", "is_active"),
        {"extend_existing": True}
    )
    
    # Primary key
    id: Mapped[PGUUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Template identification
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=False)
    
    # Categorization
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    applicable_anomaly_types: Mapped[List[str]] = mapped_column(ARRAY(String), nullable=False)
    
    # Priority and usage
    priority_default: Mapped[int] = mapped_column(Integer, nullable=False)
    times_applied: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
    # Relationships
    recommendations: Mapped[List["Recommendation"]] = relationship("Recommendation", back_populates="template")
    
    def __init__(self, **kwargs):
        """Initialize with validation."""
        super().__init__(**kwargs)
        # Validate after initialization
        if hasattr(self, 'code') and not self.code:
            raise ValueError("Template code cannot be empty")
        if hasattr(self, 'applicable_anomaly_types') and not self.applicable_anomaly_types:
            raise ValueError("Template must apply to at least one anomaly type")
        if hasattr(self, 'priority_default') and self.priority_default < 1:
            raise ValueError(f"Priority must be >= 1, got {self.priority_default}")
    
    def increment_usage(self) -> None:
        """Increment the times_applied counter and update timestamp."""
        self.times_applied += 1
        self.updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """Mark template as inactive."""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def is_applicable_to(self, anomaly_type_value: str) -> bool:
        """
        Check if this template applies to given anomaly type.
        
        Args:
            anomaly_type_value: String value of the anomaly type
            
        Returns:
            True if template applies to this anomaly type
        """
        return anomaly_type_value in self.applicable_anomaly_types

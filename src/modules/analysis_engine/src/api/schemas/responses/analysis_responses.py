"""
Response schemas for Analysis Engine API endpoints.

Pydantic models that serialize domain entities to JSON responses.
Following ADR-006 API Layer Design and ADR-020 Analysis Engine Architecture.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


# ---------------------------------------------------------------------------
# Generic wrappers
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    items: List[T] = Field(..., description="Items on the current page")
    total: int = Field(..., description="Total number of items", ge=0)
    page: int = Field(..., description="Current page number (1-indexed)", ge=1)
    size: int = Field(..., description="Items per page", ge=1, le=100)

    @property
    def total_pages(self) -> int:
        if self.size == 0:
            return 0
        return (self.total + self.size - 1) // self.size


# ---------------------------------------------------------------------------
# Anomaly response
# ---------------------------------------------------------------------------

class AnomalyResponse(BaseModel):
    """
    Response DTO for an Anomaly detected during fermentation analysis.

    Maps to the Anomaly ORM entity (domain/entities/anomaly.py).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Anomaly unique identifier")
    analysis_id: UUID = Field(..., description="Parent analysis UUID")
    sample_id: Optional[UUID] = Field(None, description="Related sample UUID, if any")

    # Classification
    anomaly_type: str = Field(..., description="Type of anomaly (see AnomalyType enum)")
    severity: str = Field(..., description="Severity level: CRITICAL | WARNING | INFO")
    description: str = Field(..., description="Human-readable description of the anomaly")

    # Metrics
    deviation_score: Dict[str, Any] = Field(
        ...,
        description="Deviation metrics: score, threshold, actual_value, expected_range"
    )

    # Resolution
    is_resolved: bool = Field(..., description="Whether the anomaly has been resolved")
    detected_at: datetime = Field(..., description="When the anomaly was detected (UTC)")
    resolved_at: Optional[datetime] = Field(None, description="When resolved (UTC), null if not yet resolved")


# ---------------------------------------------------------------------------
# Recommendation response
# ---------------------------------------------------------------------------

class RecommendationResponse(BaseModel):
    """
    Response DTO for a Recommendation generated from anomaly analysis.

    Maps to the Recommendation ORM entity (domain/entities/recommendation.py).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Recommendation unique identifier")
    analysis_id: UUID = Field(..., description="Parent analysis UUID")
    anomaly_id: Optional[UUID] = Field(None, description="Related anomaly UUID, if any")
    recommendation_template_id: UUID = Field(..., description="Template used to generate this recommendation")

    # Content
    recommendation_text: str = Field(..., description="Actionable recommendation text for the winemaker")
    priority: int = Field(..., description="Priority ranking (1=highest)", ge=1)
    confidence: float = Field(..., description="Confidence score [0-1]", ge=0, le=1)
    supporting_evidence_count: int = Field(
        ...,
        description="Number of historical data points supporting this recommendation",
        ge=0
    )

    # Application tracking
    is_applied: bool = Field(..., description="Whether the winemaker applied this recommendation")
    applied_at: Optional[datetime] = Field(None, description="When applied (UTC), null if not yet applied")


# ---------------------------------------------------------------------------
# Confidence level response
# ---------------------------------------------------------------------------

class ConfidenceLevelResponse(BaseModel):
    """
    Response DTO summarizing the confidence level of an analysis.

    Derived from the confidence_level JSONB field on Analysis.
    """

    level: str = Field(..., description="Confidence level: LOW | MEDIUM | HIGH | VERY_HIGH")
    historical_samples_count: int = Field(
        ...,
        description="Number of similar historical fermentations used",
        ge=0
    )
    similarity_score: float = Field(
        ...,
        description="Average similarity score with historical data [0-100]",
        ge=0,
        le=100
    )
    explanation: str = Field(..., description="Human-readable explanation for the winemaker")


# ---------------------------------------------------------------------------
# Analysis response
# ---------------------------------------------------------------------------

class AnalysisResponse(BaseModel):
    """
    Response DTO for a complete fermentation analysis.

    Maps to the Analysis ORM entity (domain/entities/analysis.py) and
    its nested relationships (anomalies, recommendations).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Analysis unique identifier")
    fermentation_id: UUID = Field(..., description="Fermentation that was analyzed")
    winery_id: UUID = Field(..., description="Winery that owns the analysis (multi-tenancy)")

    # Status
    status: str = Field(..., description="Analysis status: PENDING | IN_PROGRESS | COMPLETE | FAILED")
    analyzed_at: datetime = Field(..., description="When the analysis was run (UTC)")

    # Results
    comparison_result: Dict[str, Any] = Field(
        ...,
        description="Historical comparison data: similar fermentations, statistics"
    )
    confidence_level: Dict[str, Any] = Field(
        ...,
        description="Confidence metadata: level, sample count, similarity score"
    )
    historical_samples_count: int = Field(
        ...,
        description="Number of historical fermentations used in comparison",
        ge=0
    )

    # Nested relationships (loaded eagerly when available)
    anomalies: List[AnomalyResponse] = Field(
        default_factory=list,
        description="Anomalies detected in this analysis"
    )
    recommendations: List[RecommendationResponse] = Field(
        default_factory=list,
        description="Recommendations generated from detected anomalies"
    )

    @classmethod
    def from_orm_entity(cls, analysis: Any) -> "AnalysisResponse":
        """
        Build response from ORM entity, safely handling lazy-loaded relationships.

        Args:
            analysis: Analysis ORM entity

        Returns:
            AnalysisResponse serialized DTO
        """
        anomalies = []
        try:
            raw_anomalies = analysis.anomalies
            if raw_anomalies:
                anomalies = [AnomalyResponse.model_validate(a) for a in raw_anomalies]
        except Exception:
            pass  # Lazy-loaded attribute not available outside session

        recommendations = []
        try:
            raw_recs = analysis.recommendations
            if raw_recs:
                recommendations = [RecommendationResponse.model_validate(r) for r in raw_recs]
        except Exception:
            pass

        return cls(
            id=analysis.id,
            fermentation_id=analysis.fermentation_id,
            winery_id=analysis.winery_id,
            status=analysis.status,
            analyzed_at=analysis.analyzed_at,
            comparison_result=analysis.comparison_result or {},
            confidence_level=analysis.confidence_level or {},
            historical_samples_count=analysis.historical_samples_count or 0,
            anomalies=anomalies,
            recommendations=recommendations,
        )


class AnalysisSummaryResponse(BaseModel):
    """
    Lightweight analysis response for list endpoints (excludes nested relationships).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Analysis unique identifier")
    fermentation_id: UUID = Field(..., description="Fermentation that was analyzed")
    status: str = Field(..., description="Analysis status")
    analyzed_at: datetime = Field(..., description="When the analysis was run (UTC)")
    historical_samples_count: int = Field(..., description="Number of historical samples used", ge=0)
    anomaly_count: int = Field(default=0, description="Number of anomalies detected")
    recommendation_count: int = Field(default=0, description="Number of recommendations generated")

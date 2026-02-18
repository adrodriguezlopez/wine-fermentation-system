"""
Analysis Engine - Domain Enums

Enums que definen los tipos de valores permitidos en el dominio del Analysis Engine.
"""

from .anomaly_type import AnomalyType
from .severity_level import SeverityLevel
from .analysis_status import AnalysisStatus
from .recommendation_category import RecommendationCategory

__all__ = [
    "AnomalyType",
    "SeverityLevel",
    "AnalysisStatus",
    "RecommendationCategory",
]

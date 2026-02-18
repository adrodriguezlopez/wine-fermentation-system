"""
Repository interfaces for Analysis Engine domain.
"""
from .analysis_repository_interface import IAnalysisRepository
from .anomaly_repository_interface import IAnomalyRepository
from .recommendation_repository_interface import IRecommendationRepository
from .recommendation_template_repository_interface import IRecommendationTemplateRepository

__all__ = [
    "IAnalysisRepository",
    "IAnomalyRepository",
    "IRecommendationRepository",
    "IRecommendationTemplateRepository",
]

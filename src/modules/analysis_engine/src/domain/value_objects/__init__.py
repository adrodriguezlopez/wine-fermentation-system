"""
Analysis Engine - Domain Value Objects

Value Objects que encapsulan lógica de dominio sin identidad propia.
"""

from .comparison_result import ComparisonResult
from .deviation_score import DeviationScore
from .confidence_level import ConfidenceLevel

__all__ = [
    "ComparisonResult",
    "DeviationScore",
    "ConfidenceLevel",
]

"""
Value Object: ComparisonResult

Resultado de comparar fermentación actual vs patrones históricos.
Contiene métricas estadísticas y metadatos de la comparación.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass(frozen=True)
class ComparisonResult:
    """
    Resultado de comparación entre fermentación actual y patrones históricos.
    
    Attributes:
        historical_samples_count: Cantidad de fermentaciones históricas usadas en comparación
        similarity_score: Score de similitud [0-100] basado en criterios (varietal, origin, etc.)
        statistical_metrics: Dict con métricas estadísticas calculadas
        comparison_criteria: Dict con criterios usados para filtrar históricos
        patterns_used: IDs de los patterns históricos usados en comparación
        compared_at: Timestamp cuando se realizó la comparación
    """
    
    historical_samples_count: int
    similarity_score: float
    statistical_metrics: Dict[str, Any]
    comparison_criteria: Dict[str, Any]
    patterns_used: list[int]
    compared_at: datetime
    
    def __post_init__(self):
        """Valida los valores al crear la instancia."""
        if self.historical_samples_count < 0:
            raise ValueError("historical_samples_count no puede ser negativo")
        
        if not 0 <= self.similarity_score <= 100:
            raise ValueError("similarity_score debe estar entre 0 y 100")
        
        if not isinstance(self.statistical_metrics, dict):
            raise ValueError("statistical_metrics debe ser un diccionario")
        
        if not isinstance(self.comparison_criteria, dict):
            raise ValueError("comparison_criteria debe ser un diccionario")
    
    @property
    def has_sufficient_data(self) -> bool:
        """
        Retorna True si hay suficientes datos históricos para análisis estadístico.
        Threshold: ≥10 samples (según ADR-020).
        """
        return self.historical_samples_count >= 10
    
    @property
    def is_high_similarity(self) -> bool:
        """
        Retorna True si la similitud es alta (>80%).
        """
        return self.similarity_score >= 80
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el ComparisonResult a diccionario para persistencia JSON.
        """
        return {
            "historical_samples_count": self.historical_samples_count,
            "similarity_score": self.similarity_score,
            "statistical_metrics": self.statistical_metrics,
            "comparison_criteria": self.comparison_criteria,
            "patterns_used": self.patterns_used,
            "compared_at": self.compared_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComparisonResult":
        """
        Crea ComparisonResult desde diccionario (desde JSON en DB).
        """
        return cls(
            historical_samples_count=data["historical_samples_count"],
            similarity_score=data["similarity_score"],
            statistical_metrics=data["statistical_metrics"],
            comparison_criteria=data["comparison_criteria"],
            patterns_used=data["patterns_used"],
            compared_at=datetime.fromisoformat(data["compared_at"]),
        )

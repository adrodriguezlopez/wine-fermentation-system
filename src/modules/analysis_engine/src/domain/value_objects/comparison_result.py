"""
Value Object: ComparisonResult

Resultado de comparar fermentación actual vs patrones históricos.
Contiene métricas estadísticas y metadatos de la comparación.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass(frozen=True)
class ComparisonResult:
    """
    Resultado de comparación entre fermentación actual y patrones históricos.

    Attributes:
        similar_fermentation_count: Número de fermentaciones similares encontradas
        average_duration_days: Duración promedio de fermentaciones similares (días)
        average_final_gravity: Gravedad final promedio de fermentaciones similares
        similar_fermentation_ids: IDs de fermentaciones similares usadas
        comparison_basis: Criterios usados para la comparación (varietal, origin, brix)
    """

    similar_fermentation_count: int
    average_duration_days: Optional[float]
    average_final_gravity: Optional[float]
    similar_fermentation_ids: List[str] = field(default_factory=list)
    comparison_basis: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Valida los valores al crear la instancia."""
        if self.similar_fermentation_count < 0:
            raise ValueError("similar_fermentation_count no puede ser negativo")

    @property
    def has_sufficient_data(self) -> bool:
        """
        Retorna True si hay suficientes datos históricos para análisis estadístico.
        Threshold: ≥10 samples (según ADR-020).
        """
        return self.similar_fermentation_count >= 10

    @property
    def historical_samples_count(self) -> int:
        """Alias for backwards compatibility."""
        return self.similar_fermentation_count

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el ComparisonResult a diccionario para persistencia JSON.
        """
        return {
            "similar_fermentation_count": self.similar_fermentation_count,
            "average_duration_days": self.average_duration_days,
            "average_final_gravity": self.average_final_gravity,
            "similar_fermentation_ids": self.similar_fermentation_ids,
            "comparison_basis": self.comparison_basis,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ComparisonResult":
        """
        Crea ComparisonResult desde diccionario (desde JSON en DB).
        """
        return cls(
            similar_fermentation_count=data.get("similar_fermentation_count", 0),
            average_duration_days=data.get("average_duration_days"),
            average_final_gravity=data.get("average_final_gravity"),
            similar_fermentation_ids=data.get("similar_fermentation_ids", []),
            comparison_basis=data.get("comparison_basis", {}),
        )


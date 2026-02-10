"""
Value Object: DeviationScore

Score de desviación de una métrica respecto al patrón histórico.
Incluye valor actual, esperado, desviación estadística y metadatos.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class DeviationScore:
    """
    Score de desviación para una métrica específica.
    
    Attributes:
        metric_name: Nombre de la métrica (ej: "temperature", "density_rate")
        current_value: Valor actual de la métrica
        expected_value: Valor esperado basado en históricos
        deviation: Desviación respecto al esperado (puede ser absoluta o relativa)
        z_score: Z-score estadístico (si aplica, None si no hay suficientes datos)
        percentile: Percentil del valor actual en distribución histórica (0-100)
        is_significant: True si la desviación es estadísticamente significativa
    """
    
    metric_name: str
    current_value: float
    expected_value: float
    deviation: float
    z_score: Optional[float]
    percentile: float
    is_significant: bool
    
    def __post_init__(self):
        """Valida los valores al crear la instancia."""
        if not self.metric_name:
            raise ValueError("metric_name no puede estar vacío")
        
        if not 0 <= self.percentile <= 100:
            raise ValueError("percentile debe estar entre 0 y 100")
        
        if self.z_score is not None and abs(self.z_score) > 10:
            # Z-score extremadamente alto sugiere error de cálculo
            raise ValueError("z_score sospechosamente alto (>10), revisar cálculo")
    
    @property
    def deviation_percentage(self) -> float:
        """
        Retorna la desviación como porcentaje del valor esperado.
        """
        if self.expected_value == 0:
            return float('inf') if self.current_value != 0 else 0.0
        return (self.deviation / abs(self.expected_value)) * 100
    
    @property
    def is_extreme(self) -> bool:
        """
        Retorna True si la desviación es extrema (fuera de percentil 5-95).
        """
        return self.percentile < 5 or self.percentile > 95
    
    @property
    def severity_indicator(self) -> str:
        """
        Retorna un indicador de severidad basado en z-score o percentile.
        """
        if self.z_score is not None:
            abs_z = abs(self.z_score)
            if abs_z >= 3:
                return "critical"  # >3σ = extremadamente raro
            elif abs_z >= 2:
                return "warning"   # >2σ = poco común
            else:
                return "normal"    # ≤2σ = dentro de rango normal
        
        # Fallback a percentile si no hay z-score
        if self.percentile < 5 or self.percentile > 95:
            return "warning"
        return "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el DeviationScore a diccionario para persistencia JSON.
        """
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "deviation": self.deviation,
            "z_score": self.z_score,
            "percentile": self.percentile,
            "is_significant": self.is_significant,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviationScore":
        """
        Crea DeviationScore desde diccionario (desde JSON en DB).
        """
        return cls(
            metric_name=data["metric_name"],
            current_value=data["current_value"],
            expected_value=data["expected_value"],
            deviation=data["deviation"],
            z_score=data.get("z_score"),  # Puede ser None
            percentile=data["percentile"],
            is_significant=data["is_significant"],
        )

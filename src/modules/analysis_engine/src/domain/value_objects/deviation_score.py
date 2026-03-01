"""
Value Object: DeviationScore

Score de desviación de una métrica respecto al patrón histórico.
Incluye valor actual, esperado, desviación estadística y metadatos.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class DeviationScore:
    """
    Score de desviación para una métrica específica.
    
    Supports two usage modes:
    
    Mode 1 — full statistical mode (original):
        metric_name, current_value, expected_value, deviation,
        z_score, percentile, is_significant
    
    Mode 2 — simplified service mode:
        deviation, threshold, magnitude, details
    """
    
    # --- Core field (always required) ---
    deviation: float = 0.0

    # --- Full statistical mode fields ---
    metric_name: str = ""
    current_value: float = 0.0
    expected_value: float = 0.0
    z_score: Optional[float] = None
    percentile: float = 50.0
    is_significant: bool = False

    # --- Simplified service mode fields ---
    threshold: Optional[float] = None
    magnitude: Optional[str] = None          # "LOW", "MEDIUM", "HIGH"
    details: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Valida los valores al crear la instancia."""
        if self.z_score is not None and abs(self.z_score) > 10:
            # Z-score extremadamente alto sugiere error de cálculo
            raise ValueError("z_score sospechosamente alto (>10), revisar cálculo")

        if not 0 <= self.percentile <= 100:
            raise ValueError("percentile debe estar entre 0 y 100")

    @property
    def deviation_percentage(self) -> float:
        """
        Retorna la desviación como porcentaje del valor esperado.
        """
        base = self.threshold if self.threshold is not None else self.expected_value
        if base == 0:
            return float('inf') if self.deviation != 0 else 0.0
        return (self.deviation / abs(base)) * 100

    @property
    def is_extreme(self) -> bool:
        """
        Retorna True si la desviación es extrema (fuera de percentil 5-95).
        """
        return self.percentile < 5 or self.percentile > 95

    @property
    def severity_indicator(self) -> str:
        """
        Retorna un indicador de severidad basado en z-score, magnitude o percentile.
        """
        if self.magnitude:
            mag = self.magnitude.upper()
            if mag == "HIGH":
                return "critical"
            elif mag == "MEDIUM":
                return "warning"
            return "normal"

        if self.z_score is not None:
            abs_z = abs(self.z_score)
            if abs_z >= 3:
                return "critical"
            elif abs_z >= 2:
                return "warning"
            return "normal"

        if self.percentile < 5 or self.percentile > 95:
            return "warning"
        return "normal"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte el DeviationScore a diccionario para persistencia JSON.
        """
        d: Dict[str, Any] = {
            "deviation": self.deviation,
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "expected_value": self.expected_value,
            "z_score": self.z_score,
            "percentile": self.percentile,
            "is_significant": self.is_significant,
        }
        if self.threshold is not None:
            d["threshold"] = self.threshold
        if self.magnitude is not None:
            d["magnitude"] = self.magnitude
        if self.details is not None:
            d["details"] = self.details
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviationScore":
        """
        Crea DeviationScore desde diccionario (desde JSON en DB).
        """
        return cls(
            metric_name=data.get("metric_name", ""),
            current_value=data.get("current_value", 0.0),
            expected_value=data.get("expected_value", 0.0),
            deviation=data.get("deviation", 0.0),
            z_score=data.get("z_score"),
            percentile=data.get("percentile", 50.0),
            is_significant=data.get("is_significant", False),
            threshold=data.get("threshold"),
            magnitude=data.get("magnitude"),
            details=data.get("details"),
        )

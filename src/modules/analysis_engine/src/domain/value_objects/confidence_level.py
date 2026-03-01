"""
Value Object: ConfidenceLevel

Nivel de confianza del análisis basado en cantidad y calidad de datos históricos.
SIEMPRE visible al usuario (ADR-020: transparency = reliability).
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any


class ConfidenceLevelEnum(str, Enum):
    """
    Niveles de confianza del análisis.
    
    Basado en cantidad de fermentaciones históricas similares:
    - LOW: < 5 samples
    - MEDIUM: 5-15 samples
    - HIGH: 15-30 samples
    - VERY_HIGH: > 30 samples
    """
    
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    
    @property
    def label_es(self) -> str:
        """Etiqueta en español."""
        return {
            ConfidenceLevelEnum.LOW: "Bajo",
            ConfidenceLevelEnum.MEDIUM: "Medio",
            ConfidenceLevelEnum.HIGH: "Alto",
            ConfidenceLevelEnum.VERY_HIGH: "Muy Alto",
        }[self]
    
    @property
    def icon(self) -> str:
        """Emoji/icon para UI."""
        return {
            ConfidenceLevelEnum.LOW: "⚠️",
            ConfidenceLevelEnum.MEDIUM: "ℹ️",
            ConfidenceLevelEnum.HIGH: "✅",
            ConfidenceLevelEnum.VERY_HIGH: "✅✅",
        }[self]
    
    @property
    def warning_message_es(self) -> str:
        """Mensaje de advertencia para mostrar al usuario."""
        return {
            ConfidenceLevelEnum.LOW: "Datos históricos limitados - usar con precaución",
            ConfidenceLevelEnum.MEDIUM: "Datos históricos moderados",
            ConfidenceLevelEnum.HIGH: "Datos históricos sólidos",
            ConfidenceLevelEnum.VERY_HIGH: "Datos históricos muy sólidos",
        }[self]


@dataclass(frozen=True)
class ConfidenceLevel:
    """
    Nivel de confianza multi-dimensional del análisis.

    Attributes:
        overall_confidence: Score de confianza global [0.0 - 1.0]
        historical_data_confidence: Confianza basada en cantidad de datos históricos [0.0 - 1.0]
        detection_algorithm_confidence: Confianza en el algoritmo de detección [0.0 - 1.0]
        recommendation_confidence: Confianza en las recomendaciones generadas [0.0 - 1.0]
        sample_size: Número de fermentaciones históricas similares usadas
        anomalies_detected: Número de anomalías detectadas
        recommendations_generated: Número de recomendaciones generadas
    """

    overall_confidence: float
    historical_data_confidence: float
    detection_algorithm_confidence: float
    recommendation_confidence: float
    sample_size: int
    anomalies_detected: int
    recommendations_generated: int

    def __post_init__(self):
        """Valida rangos de confianza."""
        for field_name in (
            "overall_confidence",
            "historical_data_confidence",
            "detection_algorithm_confidence",
            "recommendation_confidence",
        ):
            val = getattr(self, field_name)
            if not 0.0 <= val <= 1.0:
                raise ValueError(f"{field_name} debe estar entre 0.0 y 1.0, got {val}")
        if self.sample_size < 0:
            raise ValueError("sample_size no puede ser negativo")

    # ------------------------------------------------------------------
    # Back-compat aliases
    # ------------------------------------------------------------------

    @property
    def historical_samples_count(self) -> int:
        """Alias for backwards compatibility."""
        return self.sample_size

    @property
    def level(self) -> ConfidenceLevelEnum:
        """Derive categorical level from overall_confidence."""
        if self.overall_confidence >= 0.75:
            return ConfidenceLevelEnum.VERY_HIGH
        elif self.overall_confidence >= 0.55:
            return ConfidenceLevelEnum.HIGH
        elif self.overall_confidence >= 0.35:
            return ConfidenceLevelEnum.MEDIUM
        else:
            return ConfidenceLevelEnum.LOW

    @property
    def explanation(self) -> str:
        """Human-readable explanation derived from scores."""
        return (
            f"Confianza global {self.overall_confidence:.0%} basada en "
            f"{self.sample_size} fermentaciones históricas"
        )

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    @staticmethod
    def calculate_level_from_count(count: int) -> ConfidenceLevelEnum:
        """
        Calcula el nivel de confianza basado en cantidad de samples.

        Thresholds según ADR-020:
        - LOW: < 5
        - MEDIUM: 5-15
        - HIGH: 15-30
        - VERY_HIGH: > 30
        """
        if count < 5:
            return ConfidenceLevelEnum.LOW
        elif count < 15:
            return ConfidenceLevelEnum.MEDIUM
        elif count < 30:
            return ConfidenceLevelEnum.HIGH
        else:
            return ConfidenceLevelEnum.VERY_HIGH

    @property
    def should_apply_statistical_analysis(self) -> bool:
        """
        Retorna True si hay suficientes datos para análisis estadístico (Z-score).
        Threshold: ≥10 samples según ADR-020.
        """
        return self.sample_size >= 10

    @property
    def ui_display(self) -> Dict[str, str]:
        """Retorna información para display en UI."""
        lvl = self.level
        return {
            "level": lvl.value,
            "label": lvl.label_es,
            "icon": lvl.icon,
            "warning": lvl.warning_message_es,
            "tooltip": self.explanation,
            "samples_count": str(self.sample_size),
            "overall_confidence": f"{self.overall_confidence:.0%}",
        }

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para persistencia JSON."""
        return {
            "overall_confidence": self.overall_confidence,
            "historical_data_confidence": self.historical_data_confidence,
            "detection_algorithm_confidence": self.detection_algorithm_confidence,
            "recommendation_confidence": self.recommendation_confidence,
            "sample_size": self.sample_size,
            "anomalies_detected": self.anomalies_detected,
            "recommendations_generated": self.recommendations_generated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceLevel":
        """Crea ConfidenceLevel desde diccionario (desde JSON en DB)."""
        return cls(
            overall_confidence=data.get("overall_confidence", 0.0),
            historical_data_confidence=data.get("historical_data_confidence", 0.0),
            detection_algorithm_confidence=data.get("detection_algorithm_confidence", 0.0),
            recommendation_confidence=data.get("recommendation_confidence", 0.0),
            sample_size=data.get("sample_size", data.get("historical_samples_count", 0)),
            anomalies_detected=data.get("anomalies_detected", 0),
            recommendations_generated=data.get("recommendations_generated", 0),
        )

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_comparison_result(
        cls,
        historical_samples_count: int,
        similarity_score: float,
    ) -> "ConfidenceLevel":
        """
        Crea ConfidenceLevel desde resultado de comparación.

        Uses a simple heuristic: historical_data_confidence from count,
        other confidence dimensions default to 0.8 (no anomaly/rec context).
        """
        # Historical confidence based on sample count
        if historical_samples_count >= 30:
            hist_conf = 1.0
        elif historical_samples_count >= 15:
            hist_conf = 0.8
        elif historical_samples_count >= 5:
            hist_conf = 0.6
        else:
            hist_conf = 0.3

        # Adjust slightly by similarity score
        hist_conf = round(min(1.0, hist_conf * (0.7 + 0.3 * similarity_score / 100)), 2)

        overall = round((hist_conf * 0.3 + 0.8 * 0.4 + 0.8 * 0.3), 2)

        return cls(
            overall_confidence=overall,
            historical_data_confidence=hist_conf,
            detection_algorithm_confidence=0.8,
            recommendation_confidence=0.8,
            sample_size=historical_samples_count,
            anomalies_detected=0,
            recommendations_generated=0,
        )


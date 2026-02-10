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
    Nivel de confianza del análisis con metadatos adicionales.
    
    Attributes:
        level: Nivel de confianza (LOW/MEDIUM/HIGH/VERY_HIGH)
        historical_samples_count: Cantidad exacta de samples históricos usados
        similarity_score: Score de similitud promedio con históricos [0-100]
        explanation: Texto explicativo del nivel de confianza (para tooltip/UI)
    """
    
    level: ConfidenceLevelEnum
    historical_samples_count: int
    similarity_score: float
    explanation: str
    
    def __post_init__(self):
        """Valida consistencia entre level y samples_count."""
        if self.historical_samples_count < 0:
            raise ValueError("historical_samples_count no puede ser negativo")
        
        if not 0 <= self.similarity_score <= 100:
            raise ValueError("similarity_score debe estar entre 0 y 100")
        
        # Validar consistencia entre level y count
        expected_level = self.calculate_level_from_count(self.historical_samples_count)
        if self.level != expected_level:
            raise ValueError(
                f"Inconsistencia: level={self.level} pero count={self.historical_samples_count} "
                f"debería ser level={expected_level}"
            )
    
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
    
    @classmethod
    def from_comparison_result(
        cls,
        historical_samples_count: int,
        similarity_score: float,
    ) -> "ConfidenceLevel":
        """
        Crea ConfidenceLevel desde resultado de comparación.
        """
        level = cls.calculate_level_from_count(historical_samples_count)
        
        explanation = (
            f"Basado en {historical_samples_count} fermentaciones similares "
            f"(similitud: {similarity_score:.1f}%)"
        )
        
        return cls(
            level=level,
            historical_samples_count=historical_samples_count,
            similarity_score=similarity_score,
            explanation=explanation,
        )
    
    @property
    def should_apply_statistical_analysis(self) -> bool:
        """
        Retorna True si hay suficientes datos para análisis estadístico (Z-score).
        Threshold: ≥10 samples según ADR-020.
        """
        return self.historical_samples_count >= 10
    
    @property
    def ui_display(self) -> Dict[str, str]:
        """
        Retorna información para display en UI.
        """
        return {
            "level": self.level.value,
            "label": self.level.label_es,
            "icon": self.level.icon,
            "warning": self.level.warning_message_es,
            "tooltip": self.explanation,
            "samples_count": str(self.historical_samples_count),
            "similarity": f"{self.similarity_score:.1f}%",
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convierte a diccionario para persistencia JSON.
        """
        return {
            "level": self.level.value,
            "historical_samples_count": self.historical_samples_count,
            "similarity_score": self.similarity_score,
            "explanation": self.explanation,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConfidenceLevel":
        """
        Crea ConfidenceLevel desde diccionario (desde JSON en DB).
        """
        return cls(
            level=ConfidenceLevelEnum(data["level"]),
            historical_samples_count=data["historical_samples_count"],
            similarity_score=data["similarity_score"],
            explanation=data["explanation"],
        )

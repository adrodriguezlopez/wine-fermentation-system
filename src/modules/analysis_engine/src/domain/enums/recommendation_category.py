"""
Enum: RecommendationCategory

Define las categorías de recomendaciones para organizar y filtrar acciones sugeridas.
"""

from enum import Enum


class RecommendationCategory(str, Enum):
    """
    Categorías de recomendaciones.
    
    - TEMPERATURE_ADJUSTMENT: Ajustes de temperatura (subir/bajar)
    - NUTRIENT_ADDITION: Agregar nutrientes (DAP, Fermaid, etc.)
    - RE_INOCULATION: Re-inocular con levaduras
    - AERATION: Aeración o trasiegos
    - MONITORING: Aumentar frecuencia de monitoreo
    - PREVENTIVE: Acciones preventivas futuras
    """
    
    TEMPERATURE_ADJUSTMENT = "TEMPERATURE_ADJUSTMENT"
    NUTRIENT_ADDITION = "NUTRIENT_ADDITION"
    RE_INOCULATION = "RE_INOCULATION"
    AERATION = "AERATION"
    MONITORING = "MONITORING"
    PREVENTIVE = "PREVENTIVE"
    
    @property
    def label_es(self) -> str:
        """
        Retorna la etiqueta en español de la categoría.
        """
        return {
            RecommendationCategory.TEMPERATURE_ADJUSTMENT: "Ajuste de Temperatura",
            RecommendationCategory.NUTRIENT_ADDITION: "Adición de Nutrientes",
            RecommendationCategory.RE_INOCULATION: "Re-Inoculación",
            RecommendationCategory.AERATION: "Aeración",
            RecommendationCategory.MONITORING: "Monitoreo",
            RecommendationCategory.PREVENTIVE: "Preventivo",
        }[self]
    
    @property
    def typical_urgency(self) -> str:
        """
        Retorna la urgencia típica de esta categoría.
        """
        return {
            RecommendationCategory.TEMPERATURE_ADJUSTMENT: "immediate",
            RecommendationCategory.NUTRIENT_ADDITION: "immediate",
            RecommendationCategory.RE_INOCULATION: "soon",
            RecommendationCategory.AERATION: "soon",
            RecommendationCategory.MONITORING: "routine",
            RecommendationCategory.PREVENTIVE: "future",
        }[self]

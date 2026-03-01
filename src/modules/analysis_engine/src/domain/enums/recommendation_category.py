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
    TEMPERATURE_CONTROL = "TEMPERATURE_CONTROL"
    NUTRIENT_ADDITION = "NUTRIENT_ADDITION"
    NUTRIENT_MANAGEMENT = "NUTRIENT_MANAGEMENT"
    RE_INOCULATION = "RE_INOCULATION"
    AERATION = "AERATION"
    AERATION_REMONTAGE = "AERATION_REMONTAGE"
    MONITORING = "MONITORING"
    MONITORING_FREQUENCY = "MONITORING_FREQUENCY"
    PREVENTIVE = "PREVENTIVE"
    SANITATION = "SANITATION"
    
    @property
    def label_es(self) -> str:
        """
        Retorna la etiqueta en español de la categoría.
        """
        labels = {
            RecommendationCategory.TEMPERATURE_ADJUSTMENT: "Ajuste de Temperatura",
            RecommendationCategory.TEMPERATURE_CONTROL: "Control de Temperatura",
            RecommendationCategory.NUTRIENT_ADDITION: "Adición de Nutrientes",
            RecommendationCategory.NUTRIENT_MANAGEMENT: "Gestión de Nutrientes",
            RecommendationCategory.RE_INOCULATION: "Re-Inoculación",
            RecommendationCategory.AERATION: "Aeración",
            RecommendationCategory.AERATION_REMONTAGE: "Aeración / Remontaje",
            RecommendationCategory.MONITORING: "Monitoreo",
            RecommendationCategory.MONITORING_FREQUENCY: "Frecuencia de Monitoreo",
            RecommendationCategory.PREVENTIVE: "Preventivo",
            RecommendationCategory.SANITATION: "Saneamiento",
        }
        return labels.get(self, self.value)
    
    @property
    def typical_urgency(self) -> str:
        """
        Retorna la urgencia típica de esta categoría.
        """
        urgency = {
            RecommendationCategory.TEMPERATURE_ADJUSTMENT: "immediate",
            RecommendationCategory.TEMPERATURE_CONTROL: "immediate",
            RecommendationCategory.NUTRIENT_ADDITION: "immediate",
            RecommendationCategory.NUTRIENT_MANAGEMENT: "immediate",
            RecommendationCategory.RE_INOCULATION: "soon",
            RecommendationCategory.AERATION: "soon",
            RecommendationCategory.AERATION_REMONTAGE: "soon",
            RecommendationCategory.MONITORING: "routine",
            RecommendationCategory.MONITORING_FREQUENCY: "routine",
            RecommendationCategory.PREVENTIVE: "future",
            RecommendationCategory.SANITATION: "soon",
        }
        return urgency.get(self, "routine")

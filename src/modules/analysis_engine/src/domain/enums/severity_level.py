"""
Enum: SeverityLevel

Define los niveles de severidad para anomalías y recomendaciones.
Determina la urgencia de la acción requerida.
"""

from enum import Enum


class SeverityLevel(str, Enum):
    """
    Niveles de severidad para anomalías.
    
    - CRITICAL: Requiere acción inmediata, puede arruinar el lote
    - WARNING: Requiere atención pronto, potencial problema futuro
    - INFO: Observación informativa, no requiere acción inmediata
    """
    
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    
    @property
    def priority_score(self) -> int:
        """
        Retorna un score numérico para ordenamiento (mayor = más severo).
        """
        return {
            SeverityLevel.CRITICAL: 3,
            SeverityLevel.WARNING: 2,
            SeverityLevel.INFO: 1,
        }[self]
    
    @property
    def label_es(self) -> str:
        """
        Retorna la etiqueta en español del nivel de severidad.
        """
        return {
            SeverityLevel.CRITICAL: "Crítico",
            SeverityLevel.WARNING: "Advertencia",
            SeverityLevel.INFO: "Información",
        }[self]

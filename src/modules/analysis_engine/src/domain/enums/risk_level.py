"""
Enum: RiskLevel

Define los niveles de riesgo para los advisories generados por el Analysis Engine
hacia el Protocol Engine (ADR-037 - Protocol-Analysis Integration).

El RiskLevel indica la urgencia de actuar sobre el advisory:
- CRITICAL: Acción inmediata (próximas horas)
- HIGH: Acción pronto (próximas 24h)
- MEDIUM: Monitorear de cerca (próximos días)
- LOW: Información para próxima revisión rutinaria
"""

from enum import Enum


class RiskLevel(str, Enum):
    """
    Niveles de riesgo para advisories de integración Protocol-Analysis.

    - CRITICAL: El lote puede perderse si no se actúa de inmediato
    - HIGH: Riesgo real de pérdida de calidad en las próximas 24h
    - MEDIUM: Condición que requiere monitoreo elevado
    - LOW: Observación informativa, sin urgencia
    """

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

    @property
    def priority_score(self) -> int:
        """Score numérico para ordenamiento (mayor = más urgente)."""
        return {
            RiskLevel.CRITICAL: 4,
            RiskLevel.HIGH: 3,
            RiskLevel.MEDIUM: 2,
            RiskLevel.LOW: 1,
        }[self]

    @property
    def label_es(self) -> str:
        """Etiqueta en español del nivel de riesgo."""
        return {
            RiskLevel.CRITICAL: "Crítico",
            RiskLevel.HIGH: "Alto",
            RiskLevel.MEDIUM: "Medio",
            RiskLevel.LOW: "Bajo",
        }[self]

    @property
    def action_timeframe_es(self) -> str:
        """Ventana de tiempo recomendada para actuar."""
        return {
            RiskLevel.CRITICAL: "Próximas 2 horas",
            RiskLevel.HIGH: "Próximas 24 horas",
            RiskLevel.MEDIUM: "Próximos 2-3 días",
            RiskLevel.LOW: "Próxima revisión rutinaria",
        }[self]

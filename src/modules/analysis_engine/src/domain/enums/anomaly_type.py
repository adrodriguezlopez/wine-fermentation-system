"""
Enum: AnomalyType

Define los 8 tipos de anomalías detectables en fermentaciones.
Basado en investigación científica (Wikipedia, MDPI, Frontiers in Microbiology)
y pendiente de validación por enólogo experto.

Prioridades:
- CRITICAL (3): Pueden arruinar el lote
- WARNING (3): Requieren atención pero no son inmediatamente críticos
- INFO (2): Patrones inusuales que vale la pena observar
"""

from enum import Enum


class AnomalyType(str, Enum):
    """
    Tipos de anomalías detectables en fermentaciones.
    
    Priority 1 - CRITICAL:
    - STUCK_FERMENTATION: Fermentación detenida prematuramente
    - TEMPERATURE_OUT_OF_RANGE_CRITICAL: Temperatura fuera de límites absolutos
    - VOLATILE_ACIDITY_HIGH: Acidez volátil (ácido acético) elevada
    
    Priority 2 - WARNING:
    - DENSITY_DROP_TOO_FAST: Caída de densidad demasiado rápida
    - HYDROGEN_SULFIDE_RISK: Condiciones favorables para H₂S
    - TEMPERATURE_SUBOPTIMAL: Temperatura fuera del rango óptimo
    
    Priority 3 - INFO:
    - UNUSUAL_DURATION: Duración fuera del percentil 10-90
    - ATYPICAL_PATTERN: Patrón de densidad fuera de banda de confianza ±2σ
    """
    
    # Priority 1 - CRITICAL
    STUCK_FERMENTATION = "STUCK_FERMENTATION"
    TEMPERATURE_OUT_OF_RANGE_CRITICAL = "TEMPERATURE_OUT_OF_RANGE_CRITICAL"
    VOLATILE_ACIDITY_HIGH = "VOLATILE_ACIDITY_HIGH"
    
    # Priority 2 - WARNING
    DENSITY_DROP_TOO_FAST = "DENSITY_DROP_TOO_FAST"
    HYDROGEN_SULFIDE_RISK = "HYDROGEN_SULFIDE_RISK"
    TEMPERATURE_SUBOPTIMAL = "TEMPERATURE_SUBOPTIMAL"
    
    # Priority 3 - INFO
    UNUSUAL_DURATION = "UNUSUAL_DURATION"
    ATYPICAL_PATTERN = "ATYPICAL_PATTERN"
    
    @property
    def priority(self) -> int:
        """
        Retorna la prioridad del tipo de anomalía (1=CRITICAL, 2=WARNING, 3=INFO).
        """
        if self in (
            AnomalyType.STUCK_FERMENTATION,
            AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL,
            AnomalyType.VOLATILE_ACIDITY_HIGH,
        ):
            return 1
        elif self in (
            AnomalyType.DENSITY_DROP_TOO_FAST,
            AnomalyType.HYDROGEN_SULFIDE_RISK,
            AnomalyType.TEMPERATURE_SUBOPTIMAL,
        ):
            return 2
        else:
            return 3
    
    @property
    def description(self) -> str:
        """
        Retorna una descripción en español del tipo de anomalía.
        """
        descriptions = {
            AnomalyType.STUCK_FERMENTATION: "Fermentación detenida sin alcanzar densidad objetivo",
            AnomalyType.TEMPERATURE_OUT_OF_RANGE_CRITICAL: "Temperatura fuera de límites críticos (<15°C o >32°C)",
            AnomalyType.VOLATILE_ACIDITY_HIGH: "Acidez volátil elevada (desarrollo de ácido acético)",
            AnomalyType.DENSITY_DROP_TOO_FAST: "Caída de densidad excesivamente rápida",
            AnomalyType.HYDROGEN_SULFIDE_RISK: "Condiciones que favorecen desarrollo de H₂S",
            AnomalyType.TEMPERATURE_SUBOPTIMAL: "Temperatura fuera del rango óptimo pero aceptable",
            AnomalyType.UNUSUAL_DURATION: "Duración atípica comparada con históricos",
            AnomalyType.ATYPICAL_PATTERN: "Patrón de fermentación diferente al esperado",
        }
        return descriptions[self]

"""
Enum: AnalysisStatus

Define los estados posibles de un análisis de fermentación.
"""

from enum import Enum


class AnalysisStatus(str, Enum):
    """
    Estados del ciclo de vida de un análisis.
    
    - PENDING: Análisis creado pero no ejecutado
    - IN_PROGRESS: Análisis en ejecución
    - COMPLETED: Análisis finalizado con éxito
    - FAILED: Análisis falló por error
    """
    
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    
    @property
    def is_final(self) -> bool:
        """
        Retorna True si el estado es final (no cambiará más).
        """
        return self in (AnalysisStatus.COMPLETED, AnalysisStatus.FAILED)
    
    @property
    def label_es(self) -> str:
        """
        Retorna la etiqueta en español del estado.
        """
        return {
            AnalysisStatus.PENDING: "Pendiente",
            AnalysisStatus.IN_PROGRESS: "En progreso",
            AnalysisStatus.COMPLETED: "Completado",
            AnalysisStatus.FAILED: "Fallido",
        }[self]

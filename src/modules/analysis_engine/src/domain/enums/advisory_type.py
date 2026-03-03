"""
Enum: AdvisoryType

Define los tipos de advisories que el Analysis Engine puede emitir
hacia el Protocol Engine (ADR-037 - Protocol-Analysis Integration).

Un advisory es una sugerencia de ajuste sobre el protocolo activo,
basada en anomalías detectadas durante el análisis de fermentación.
"""

from enum import Enum


class AdvisoryType(str, Enum):
    """
    Tipos de advisory emitidos por el Analysis Engine al Protocol Engine.

    - ACCELERATE_STEP: Realizar el paso antes de lo planificado
      (ej: fermentación estancada → añadir nutrientes ahora)
    - SKIP_STEP: El paso ya no es necesario
      (ej: fermentación completada → omitir chequeo de H2S)
    - ADD_STEP: Insertar un paso no planificado
      (ej: acidez volátil alta → agregar paso de saneamiento)
    """

    ACCELERATE_STEP = "ACCELERATE_STEP"
    SKIP_STEP = "SKIP_STEP"
    ADD_STEP = "ADD_STEP"

    @property
    def label_es(self) -> str:
        """Etiqueta en español del tipo de advisory."""
        return {
            AdvisoryType.ACCELERATE_STEP: "Acelerar Paso",
            AdvisoryType.SKIP_STEP: "Omitir Paso",
            AdvisoryType.ADD_STEP: "Agregar Paso",
        }[self]

    @property
    def description_es(self) -> str:
        """Descripción extendida en español."""
        return {
            AdvisoryType.ACCELERATE_STEP: (
                "El análisis sugiere realizar este paso antes de lo planificado "
                "para evitar pérdida de calidad o detención de la fermentación."
            ),
            AdvisoryType.SKIP_STEP: (
                "El análisis indica que este paso ya no es necesario "
                "dadas las condiciones actuales de la fermentación."
            ),
            AdvisoryType.ADD_STEP: (
                "El análisis detectó una condición que requiere un paso adicional "
                "no contemplado originalmente en el protocolo."
            ),
        }[self]

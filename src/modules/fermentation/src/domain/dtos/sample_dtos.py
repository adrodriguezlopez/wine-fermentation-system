"""
Sample Data Transfer Objects.

Pure Python dataclasses for sample data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).
"""

from dataclasses import dataclass
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


@dataclass
class SampleCreate:
    """
    Data transfer object for creating new samples.
    
    The repository will determine the appropriate sample type (sugar/temperature/density)
    based on the sample_type field.
    
    Attributes:
        recorded_by_user_id: ID of user recording the sample (from auth context)
        sample_type: Type of sample (SUGAR, TEMPERATURE, DENSITY)
        value: Measured value
    """
    recorded_by_user_id: int
    sample_type: SampleType
    value: float

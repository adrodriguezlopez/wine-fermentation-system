"""
Sample Data Transfer Objects.

Pure Python dataclasses for sample data transfer between layers.
No framework dependencies (no Pydantic, no SQLAlchemy).
"""

from dataclasses import dataclass
from datetime import datetime
from src.modules.fermentation.src.domain.enums.sample_type import SampleType


@dataclass
class SampleCreate:
    """
    Data transfer object for creating new samples.
    
    The repository will determine the appropriate sample type (sugar/temperature/density)
    based on the sample_type field.
    
    Attributes:
        sample_type: Type of sample (SUGAR, TEMPERATURE, DENSITY)
        value: Measured value
        units: Units of measurement (e.g., 'brix', '°C', 'g/L')
        recorded_at: Timestamp when sample was recorded
        
    Note: recorded_by_user_id is added by the service from auth context
    """
    sample_type: SampleType
    value: float
    units: str
    recorded_at: datetime

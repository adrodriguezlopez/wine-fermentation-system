from datetime import datetime
from pydantic import BaseModel, Field
from ...enums.sample_type import SampleType

class SampleBase(BaseModel):
    """Base schema for all sample types."""
    fermentation_id: int = Field(..., gt=0)
    recorded_at: datetime
    sample_type: SampleType
    value: float = Field(..., description="Measurement value")
from typing import Optional, Union
from pydantic import BaseModel
from datetime import datetime


class ValidationError(BaseModel):
    """Individual validation error with context."""

    field: str
    message: str
    current_value: Optional[Union[float, str, datetime]] = None
    expected_range: Optional[str] = None

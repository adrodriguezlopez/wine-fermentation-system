from typing import Optional
from pydantic import BaseModel


class ValidationError(BaseModel):
    """Individual validation error with context."""

    field: str
    message: str
    current_value: Optional[float] = None
    expected_range: Optional[str] = None

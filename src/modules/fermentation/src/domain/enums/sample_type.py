from enum import Enum


class SampleType(str, Enum):
    """Supported sample measurement types."""

    SUGAR = "sugar"
    TEMPERATURE = "temperature"
    DENSITY = "density"

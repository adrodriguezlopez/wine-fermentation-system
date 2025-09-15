from typing import Any
from domain.entities.samples.base_sample import BaseSample


class CelsiusTemperatureSample(BaseSample):
    """Temperature measurement in Celsius."""

    __mapper_args__ = {
        "polymorphic_identity": "temperature",
    }

    def __init__(self, **kwargs: Any) -> None:
        kwargs["units"] = "°C"
        super().__init__(**kwargs)

from typing import Any
from .base_sample import BaseSample


class DensitySample(BaseSample):
    """Density measurement in specific gravity"""

    __mapper_args__ = {
        "polymorphic_identity": "density",
    }

    def __init__(self, **kwargs: Any) -> None:
        kwargs["units"] = "specific_gravity"
        super().__init__(**kwargs)

from typing import Any
from .base_sample import BaseSample


class SugarSample(BaseSample):
    """Sugar content measurement in Brix."""

    __mapper_args__ = {
        "polymorphic_identity": "sugar",
    }

    def __init__(self, **kwargs: Any) -> None:
        # Only set default units if not provided
        if "units" not in kwargs:
            kwargs["units"] = "brix"
        super().__init__(**kwargs)

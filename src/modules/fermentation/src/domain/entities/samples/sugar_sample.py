from typing import Any
from domain.entities.samples.base_sample import BaseSample


class SugarSample(BaseSample):
    """Sugar content measurement in Brix."""

    __mapper_args__ = {
        "polymorphic_identity": "sugar",
    }

    def __init__(self, **kwargs: Any) -> None:
        kwargs["units"] = "brix"
        super().__init__(**kwargs)

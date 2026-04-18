from typing import Any

from .base_sample import BaseSample


class AceticAcidSample(BaseSample):
    """Acetic acid (volatile acidity) measurement in g/L."""

    __mapper_args__ = {"polymorphic_identity": "acetic_acid"}

    def __init__(self, **kwargs: Any) -> None:
        # Units are always g/L for acetic acid — override any caller-supplied value.
        kwargs["units"] = "g/L"
        super().__init__(**kwargs)

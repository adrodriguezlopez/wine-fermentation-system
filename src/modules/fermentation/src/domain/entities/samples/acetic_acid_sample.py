from typing import Any
from src.modules.fermentation.src.domain.entities.samples.base_sample import BaseSample


class AceticAcidSample(BaseSample):
    """Acetic acid (volatile acidity) measurement in g/L.

    Measures the primary volatile acid in wine. The value field (inherited
    from BaseSample) stores the concentration in grams per litre.

    Normal range: < 0.6 g/L
    Warning:      0.6 – 0.8 g/L
    Critical:     > 0.8 g/L  (acetification risk — immediate intervention required)

    Future samples to add with the same pattern:
      - LacticAcidSample    (g/L)  — malolactic fermentation monitoring
      - SulfurDioxideSample (mg/L) — SO₂ preservation monitoring

    Expert validation: Susana Rodriguez Vasquez (LangeTwins Winery, 20 years experience)
    """

    __mapper_args__ = {"polymorphic_identity": "acetic_acid"}

    def __init__(self, **kwargs: Any) -> None:
        # Units are always g/L for acetic acid — override any caller-supplied value.
        kwargs["units"] = "g/L"
        super().__init__(**kwargs)

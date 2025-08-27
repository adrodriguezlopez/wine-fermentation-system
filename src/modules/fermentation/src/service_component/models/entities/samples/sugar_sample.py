from modules.fermentation.src.service_component.models.entities.samples.base_sample import BaseSample


class SugarSample(BaseSample):
    """Sugar content measurement in Brix."""
    __mapper_args__ = {
        "polymorphic_identity": "sugar",
    }

    def __init__(self, **kwargs):
        kwargs['units'] = 'brix'
        super().__init__(**kwargs)

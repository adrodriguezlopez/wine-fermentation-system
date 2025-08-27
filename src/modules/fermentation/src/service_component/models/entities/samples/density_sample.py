from modules.fermentation.src.service_component.models.entities.samples.base_sample import BaseSample


class DensitySample(BaseSample):
    """Density measurement in specific gravity"""
    __mapper_args__ = {
        "polymorphic_identity": "density",
    }

    def __init__(self, **kwargs):
        kwargs['units'] = 'specific_gravity'
        super().__init__(**kwargs)

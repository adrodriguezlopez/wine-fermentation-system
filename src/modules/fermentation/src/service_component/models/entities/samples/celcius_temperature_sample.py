from modules.fermentation.src.service_component.models.entities.samples.base_sample import BaseSample


class CelciusTemperatureSample(BaseSample):
    """Temperature measurement in Celsius."""
    __mapper_args__ = {
        "polymorphic_identity": "temperature",
    }

    def __init__(self, **kwargs):
        kwargs['units'] = '°C'
        super().__init__(**kwargs)

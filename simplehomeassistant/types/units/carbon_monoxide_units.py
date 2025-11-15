from simplehomeassistant.types.units.base import PartsPerMillionBase, MicrogramPerCubicMeterBase


class CarbonMonoxideSensorUnit(PartsPerMillionBase):
    MICROGRAM_PER_CUBIC_METER = MicrogramPerCubicMeterBase.MICROGRAM_PER_CUBIC_METER
    MILLIGRAM_PER_CUBIC_METER = "mg/m³"


class CarbonMonoxideNumberUnit(PartsPerMillionBase):
    pass

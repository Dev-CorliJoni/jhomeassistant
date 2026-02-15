from jhomeassistant.types.units.base import BaseUnit


class CarbonMonoxideSensorUnit(BaseUnit):
    PARTS_PER_MILLION = "ppm"
    MICROGRAM_PER_CUBIC_METER = "µg/m³"
    MILLIGRAM_PER_CUBIC_METER = "mg/m³"


class CarbonMonoxideNumberUnit(BaseUnit):
    PARTS_PER_MILLION = "ppm"

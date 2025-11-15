from enum import Enum
from simplehomeassistant.types.units.no_units import NoUnit


class BaseDeviceClass(Enum):
    @property
    def unit(self):
        return NoUnit

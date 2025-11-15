from .no_units import NoUnit
from simplehomeassistant.types.units.base import PercentageBase


class PowerFactorUnit(NoUnit):
    PERCENTAGE = PercentageBase.PERCENTAGE.value

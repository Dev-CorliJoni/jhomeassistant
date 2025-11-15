from simplehomeassistant.types.device_classes import NumberDeviceClass
from simplehomeassistant.types.units import ConductivityUnit, TemperatureDeltaUnit, CarbonMonoxideSensorUnit, \
    PressureSensorUnit, VolumeFlowRateSensorUnit, WindSpeedUnit


class SensorDeviceClass(NumberDeviceClass):
    CONDUCTIVITY = "conductivity"
    DATE = "date"
    ENUM = "enum"
    TEMPERATURE_DELTA = "temperature_delta"
    TIMESTAMP = "timestamp"

    @property
    def unit(self):
        return {
            NumberDeviceClass.CARBON_MONOXIDE: CarbonMonoxideSensorUnit,
            SensorDeviceClass.CONDUCTIVITY: ConductivityUnit,
            NumberDeviceClass.PRESSURE: PressureSensorUnit,
            NumberDeviceClass.VOLUME_FLOW_RATE: VolumeFlowRateSensorUnit,
            SensorDeviceClass.TEMPERATURE_DELTA: TemperatureDeltaUnit,
        }.get(self, super().unit)

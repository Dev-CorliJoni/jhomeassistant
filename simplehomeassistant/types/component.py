from enum import Enum

from simplehomeassistant.types.device_classes import SensorDeviceClass, NumberDeviceClass, BinarySensorDeviceClass, \
    ButtonDeviceClass, CoverDeviceClass, EventDeviceClass, ValveDeviceClass, UpdateDeviceClass, SwitchDeviceClass, \
    MediaPlayerDeviceClass, HumidifierDeviceClass


class Component(Enum):
    BINARY_SENSOR = "binary_sensor"
    BUTTON = "button"
    COVER = "cover"
    EVENT = "event"
    HUMIDIFIER = "humidifier"
    MEDIA_PLAYER = "media_player"
    NUMBER = "number"
    SENSOR = "sensor"
    SWITCH = "switch"
    UPDATE = "update"
    VALVE = "valve"

    @property
    def device_class(self):
        return {
            Component.SENSOR: SensorDeviceClass,
            Component.NUMBER: NumberDeviceClass,
            Component.BINARY_SENSOR: BinarySensorDeviceClass,
            Component.BUTTON: ButtonDeviceClass,
            Component.COVER: CoverDeviceClass,
            Component.EVENT: EventDeviceClass,
            Component.HUMIDIFIER: HumidifierDeviceClass,
            Component.MEDIA_PLAYER: MediaPlayerDeviceClass,
            Component.SWITCH: SwitchDeviceClass,
            Component.UPDATE: UpdateDeviceClass,
            Component.VALVE: ValveDeviceClass,
        }[self]

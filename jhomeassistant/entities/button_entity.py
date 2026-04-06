from __future__ import annotations
from typing import Callable

from jhomeassistant.entities.commandable_entity import CommandableEntity
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component
from jhomeassistant.types.device_classes import ButtonDeviceClass


class ButtonEntity(CommandableEntity):
    """A stateless button entity. Pressing it in HA publishes to the command_topic."""

    def __init__(self,
                 name: str,
                 command_topic: str,
                 on_press: Callable,
                 device_class: ButtonDeviceClass = ButtonDeviceClass.NONE) -> None:
        super().__init__(Component.BUTTON, name,
                         command_topic=command_topic, on_command=on_press)
        self._device_class = device_class

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        if self._device_class is not ButtonDeviceClass.NONE:
            payload[Abbreviation.DEVICE_CLASS] = self._device_class.value
        return payload

from __future__ import annotations

import json
from typing import Callable

from jhomeassistant.entities.commandable_entity import CommandableEntity
from jhomeassistant.entities.stateful_entity import StatefulEntity
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component
from jhomeassistant.types.device_classes import UpdateDeviceClass


class UpdateEntity(StatefulEntity, CommandableEntity):
    """A firmware/software update entity. Publishes version state and receives install commands.

    MRO: UpdateEntity -> StatefulEntity -> CommandableEntity -> HomeAssistantEntityBase
    """

    def __init__(self,
                 name: str,
                 state_topic: str,
                 command_topic: str | None = None,
                 on_install: Callable | None = None,
                 device_class: UpdateDeviceClass = UpdateDeviceClass.NONE) -> None:
        super().__init__(Component.UPDATE, name,
                         state_topic=state_topic,
                         command_topic=command_topic,
                         on_command=on_install)
        self._device_class = device_class

    def publish(self, installed_version: str, latest_version: str) -> None:
        payload = json.dumps({
            "installed_version": installed_version,
            "latest_version": latest_version,
        }, separators=(",", ":"))
        self._publish_state(payload)

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        if self._device_class is not UpdateDeviceClass.NONE:
            payload[Abbreviation.DEVICE_CLASS] = self._device_class.value
        return payload

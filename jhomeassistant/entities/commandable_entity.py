from __future__ import annotations
from typing import Any, Callable

from jhomeassistant.entities.homeassistant_entity_base import HomeAssistantEntityBase, MQTTConnection
from jhomeassistant.helper import validate_topic
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component


class CommandableEntity(HomeAssistantEntityBase):
    """Base for entities that receive commands via a command_topic."""

    def __init__(self, component: Component, name: str, *, command_topic: str, on_command: Callable, **kwargs: Any) -> None:
        super().__init__(component, name, **kwargs)
        self._command_topic: str = validate_topic(command_topic)
        self._on_command = on_command

    def mqtt_connected(self, get_connection: Callable[[], MQTTConnection]) -> None:
        super().mqtt_connected(get_connection)
        self._get_connection().subscribe(self._command_topic, self._on_command)

    @property
    def internal_discovery_payload(self) -> dict:
        return {
            **super().internal_discovery_payload,
            Abbreviation.COMMAND_TOPIC: self._command_topic,
        }

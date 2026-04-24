from __future__ import annotations
from typing import Any, Callable

from jhomeassistant.entities.homeassistant_entity_base import HomeAssistantEntityBase, MQTTConnection
from jhomeassistant.helper import validate_topic
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component


class CommandableEntity(HomeAssistantEntityBase):
    """Base for entities that receive commands via a command_topic."""

    def __init__(self, component: Component, name: str, *, command_topic: str | None = None, on_command: Callable | None = None, **kwargs: Any) -> None:
        super().__init__(component, name, **kwargs)
        self._command_topic: str | None = validate_topic(command_topic) if command_topic is not None else None
        self._on_command = on_command

    def mqtt_connected(self, get_connection: Callable[[], MQTTConnection]) -> None:
        super().mqtt_connected(get_connection)
        if self._command_topic is not None:
            self._get_connection().subscribe(self._command_topic, self._on_command)

    def cleanup(self, connection: MQTTConnection) -> None:
        if self._command_topic is not None:
            connection.unsubscribe(self._command_topic)

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        if self._command_topic is not None:
            payload[Abbreviation.COMMAND_TOPIC] = self._command_topic
        return payload

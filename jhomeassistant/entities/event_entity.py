from __future__ import annotations

import json
from typing import Any, List

from jhomeassistant.entities.stateful_entity import StatefulEntity
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component
from jhomeassistant.types.device_classes import EventDeviceClass


class EventEntity(StatefulEntity):
    """An event entity that publishes event payloads to its state_topic."""

    def __init__(self,
                 name: str,
                 state_topic: str,
                 event_types: List[str],
                 device_class: EventDeviceClass = EventDeviceClass.NONE) -> None:
        super().__init__(Component.EVENT, name, state_topic=state_topic)
        self._event_types = event_types
        self._device_class = device_class

    def publish(self, event_type: str, **attributes: Any) -> None:
        payload = json.dumps({"event_type": event_type, **attributes}, separators=(",", ":"))
        self._connection.publish(self._state_topic, payload)

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        payload[Abbreviation.EVENT_TYPES] = self._event_types
        if self._device_class is not EventDeviceClass.NONE:
            payload[Abbreviation.DEVICE_CLASS] = self._device_class.value
        return payload

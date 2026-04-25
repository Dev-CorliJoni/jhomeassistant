from __future__ import annotations
from typing import Any

from jmqtt import QualityOfService as QoS

from jhomeassistant.entities.homeassistant_entity_base import HomeAssistantEntityBase
from jhomeassistant.helper import validate_topic
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component


class StatefulEntity(HomeAssistantEntityBase):
    """Base for entities that publish state to a state_topic."""

    def __init__(self, component: Component, name: str, *, state_topic: str, **kwargs: Any) -> None:
        super().__init__(component, name, **kwargs)
        self._state_topic: str = validate_topic(state_topic)

    @property
    def internal_discovery_payload(self) -> dict:
        return {
            **super().internal_discovery_payload,
            Abbreviation.STATE_TOPIC: self._state_topic,
        }

    def _publish_state(
        self,
        payload: str,
        qos: QoS = QoS.AtMostOnce,
        retain: bool = False,
        wait_for_publish: bool = False,
    ) -> None:
        self._get_connection().publish(self._state_topic, payload, qos, retain, wait_for_publish=wait_for_publish)

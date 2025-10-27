from __future__ import annotations
from typing import List

from simplehomeassistant.helper import collect_ha_device_facts, build_identifier
from simplehomeassistant.entities import HomeAssistantEntityBase


class HomeAssistantDevice:
    def __init__(self, name: str, prevent_device_merge=False):
        identifiers = []
        serial_number, connections = collect_ha_device_facts(prevent_device_merge)
        if serial_number is not None:
            identifiers.append(build_identifier(serial_number))
        """elif len(connections) > 0:
            for type_, value in connections:
                if
            first = connections.pop()[1]
            identifiers.append(serial_number)"""

        self._device_discovery_payload = {
            "name": name,
            "identifiers": identifiers,
        }

        if not prevent_device_merge or len(connections) > 0:
            self._device_discovery_payload["connections"] = connections
        if serial_number is not None:
            self._device_discovery_payload["serial_number"] = serial_number

        self._entities: List[HomeAssistantEntityBase] = []

    def device_identifiers(self, *identifiers: str, append=False) -> HomeAssistantDevice:
        if append:
            self._device_discovery_payload["identifiers"].extend(identifiers)
        else:
            self._device_discovery_payload["identifiers"] = list(identifiers)
        return self

    def device_manufacturer(self, manufacturer: str) -> HomeAssistantDevice:
        self._device_discovery_payload["manufacturer"] = manufacturer
        return self

    def device_model(self, model: str) -> HomeAssistantDevice:
        self._device_discovery_payload["model"] = model
        return self

    def device_model_id(self, model_id: str) -> HomeAssistantDevice:
        self._device_discovery_payload["model_id"] = model_id
        return self

    def device_hw_version(self, hw_version: str) -> HomeAssistantDevice:
        self._device_discovery_payload["hw_version"] = hw_version
        return self

    def device_sw_version(self, sw_version: str) -> HomeAssistantDevice:
        self._device_discovery_payload["sw_version"] = sw_version
        return self

    def device_via_device(self, via_device: str) -> HomeAssistantDevice:
        self._device_discovery_payload["via_device"] = via_device
        return self

    def add_entities(self, *entities: HomeAssistantEntityBase) -> HomeAssistantDevice:
        for entity in entities:
            if not entity.has_node_id:
                entity.node_id(self._device_discovery_payload["name"].strip().replace(" ", "_"))
            self._entities.append(entity)
        return self

    def discovery_gen(self, discovery_prefix):
        for entity in self._entities:
            discovery_topic = f"{discovery_prefix}/{entity.relative_discovery_prefix}"
            discovery_payload = {
                **entity.discovery_payload,
                "device": self._device_discovery_payload,
                "unique_id": f"{self._device_discovery_payload['identifiers']}-{entity.relative_unique_id}"
            }

            yield discovery_topic, discovery_payload

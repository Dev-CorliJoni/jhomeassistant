from __future__ import annotations
from typing import List

from simplemqtt import QualityOfService as QoS
from simplehomeassistant.features import Availability
from simplehomeassistant.helper import collect_ha_device_facts, build_identifier, get_default_entity_id, \
    validate_non_empty_string
from simplehomeassistant.entities import HomeAssistantEntityBase
from simplehomeassistant.helper.abbreviations import DeviceAbbreviation, Abbreviation
from simplehomeassistant.setup_logging import get_logger as _get_logger

logger = _get_logger("HomeAssistantDevice")


def get_identifier_default(serial_number, connections, prevent_device_merge=False):
    identifiers = []
    if not prevent_device_merge:
        if serial_number is not None:
            identifiers.append(build_identifier(serial_number))

        # Priority: mac > bluetooth; within type pick smallest value for stability
        for _, value in sorted(
                connections,
                key=lambda x: ((0 if x[0] == "mac" else 1 if x[0] == "bluetooth" else 2), x[1])
        ):
            identifiers.append(build_identifier(value))
            break
    return identifiers


class HomeAssistantDevice:
    def __init__(self, name: str, prevent_device_merge=False):
        validate_non_empty_string(name, "Device 'name'")

        self.name = name
        self.serial_number, self.connections = collect_ha_device_facts(prevent_device_merge)
        self.identifiers: List[str] = get_identifier_default(self.serial_number, self.connections, prevent_device_merge)

        if not self.identifiers:
            logger.error("No device identifiers could be derived. Set at least one identifier explicitly before discovery.")
        else:
            logger.info(f"Using device identifiers for {self.name}: {self.identifiers}")

        self.manufacturer: str | None = None
        self.model: str | None = None
        self.model_id: str | None = None
        self.hw_version: str | None = None
        self.sw_version: str | None = None
        self.via_device: str | None = None
        self.configuration_url: str | None = None

        self.qos: QoS | None = None
        self.encoding: str | None = None

        self.availability = Availability()
        self._entities: List[HomeAssistantEntityBase] = []

    def _to_dict(self):
        result = {
            DeviceAbbreviation.NAME: self.name,
            DeviceAbbreviation.IDS: self.identifiers,
        }

        if len(self.connections) > 0:
            result[DeviceAbbreviation.CONNECTIONS] = self.connections

        for abbr, value in (
                (DeviceAbbreviation.SERIAL_NUMBER, self.serial_number),
                (DeviceAbbreviation.MANUFACTURER, self.manufacturer),
                (DeviceAbbreviation.MODEL, self.model),
                (DeviceAbbreviation.MODEL_ID, self.model_id),
                (DeviceAbbreviation.HW, self.hw_version),
                (DeviceAbbreviation.SW, self.sw_version),
                (DeviceAbbreviation.VIA_DEVICE, self.via_device),
                (DeviceAbbreviation.URL, self.configuration_url),
        ):
            if value is not None:
                result[abbr] = value

        return {
            Abbreviation.DEVICE: result
        }

    @property
    def unique_id(self):
        return build_identifier(self.identifiers[0], 32, self.name)

    @property
    def entities(self) -> List[HomeAssistantEntityBase]:
        return self._entities

    def add_entities(self, *entities: HomeAssistantEntityBase) -> HomeAssistantDevice:
        self._entities.extend(entities)
        logger.info(f"Added {len(entities)} entities to device {self.name}. Total={len(self._entities),}")
        return self

    def internal_discovery(self, discovery_prefix):
        if len(self.identifiers) == 0:
            raise ValueError("At least one identifier must be specified. Use HomeAssistantDevice.identifiers to set one.")

        discovery_topic = f"{discovery_prefix}/device/{self.unique_id}/config"
        include_root_availability = not all(e.availability.active for e in self._entities)

        discovery_payload = {
            **self._to_dict(),
            Abbreviation.COMPONENTS: {},
            **(self.availability.internal_to_dict() if include_root_availability else {}),
        }

        if self.qos is not None:
            discovery_payload["qos"] = self.qos.value
        if self.encoding is not None:
            discovery_payload[Abbreviation.ENCODING] = self.encoding

        entity_ids: set[str] = set()
        for entity in self._entities:
            unique_id = f"{self.unique_id}-{entity.identifier}"
            default_entity_id = get_default_entity_id(entity.platform, self.name, entity.name)

            if unique_id in entity_ids:
                raise ValueError(f"Duplicate entity identifier({unique_id}) within device({self.name}). " +
                                 f"Entity names must yield unique identifiers per device. Either update device.identifiers[0] or entity.name")
            entity_ids.add(unique_id)

            if entity.availability.active:
                entity.availability.internal_merge(self.availability)

            discovery_payload[Abbreviation.COMPONENTS][unique_id] = {
                Abbreviation.UNIQUE_ID: unique_id,
                Abbreviation.DEFAULT_ENTITY_ID: default_entity_id,
                **entity.internal_discovery_payload
            }

        return discovery_topic, discovery_payload

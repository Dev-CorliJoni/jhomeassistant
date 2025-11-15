from __future__ import annotations

import json
from typing import List, Union
from simplemqtt import QualityOfService as QoS, MQTTMessage
from simplemqtt.mqtt_connections import MQTTConnectionV3, MQTTConnectionV5

from simplehomeassistant.features import Availability, Origin, TopicConfig
from simplehomeassistant.helper import validate_discovery_prefix
from simplehomeassistant.helper.abbreviations import resolve_abbreviation
from simplehomeassistant.helper.scheduler import Scheduler, Schedule
from simplehomeassistant.homeassistant_device import HomeAssistantDevice
from simplehomeassistant.setup_logging import get_logger


logger = get_logger("HomeAssistantConnection")


def resolve_abbreviations(payload: dict, use_abbreviated_device_discovery: bool) -> dict:
    new_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            value = resolve_abbreviations(value, use_abbreviated_device_discovery)
        if not isinstance(key, str):
            key = resolve_abbreviation(key, use_abbreviated_device_discovery)

        new_payload[key] = value
    return new_payload


class HomeAssistantConnection:
    def __init__(self, connection: Union[MQTTConnectionV3, MQTTConnectionV5], use_abbreviated_device_discovery=False):
        self._use_abbreviated_device_discovery = use_abbreviated_device_discovery
        self._connection = connection
        self._devices: List[HomeAssistantDevice] = []
        self._discovery_prefix = 'homeassistant'

        self.origin = Origin()
        self.availability = Availability(self._connection.availability_topic)
        self.ha_status = TopicConfig("homeassistant/status")
        self.qos: QoS | None = None
        self.encoding: str | None = None

    def discovery_prefix(self, discovery_prefix: str) -> HomeAssistantConnection:
        self._discovery_prefix = validate_discovery_prefix(discovery_prefix)
        return self

    def add_devices(self, *devices: HomeAssistantDevice) -> HomeAssistantConnection:
        for device in devices:
            self._devices.append(device)
        return self

    def _discovery_gen(self):
        for device in self._devices:
            # Origin fallback
            if self.origin.name is None:
                logger.info(f"Using device name {device.name} as origin.name because no custom name was provided.")
                self.origin.name = device.name

            # Inherit connection-level QoS/encoding if set
            if device.qos is None and self.qos is not None:
                device.qos = self.qos
                logger.info(f"Inherit connection QoS={self.qos.name} to device {device.name}")
            if device.encoding is None and self.encoding is not None:
                device.encoding = self.encoding
                logger.info(f"Inherit connection encoding={self.encoding} to device {device.name}")

            device.availability.internal_merge(self.availability)
            discovery_topic, discovery_payload = device.internal_discovery(self._discovery_prefix)

            discovery_payload = {
                **discovery_payload,
                **self.origin.internal_to_dict()
            }

            yield discovery_topic, resolve_abbreviations(discovery_payload, self._use_abbreviated_device_discovery)

    def discovery_text(self):
        text = ""
        for topic, payload in self._discovery_gen():
            text += f"-------------------------- Topic: {topic} --------------------------\n{payload}"

    def _discovery(self, publish_timeout):
        """Publish all discovery payloads and wait for completion."""
        discovery_infos = []
        for discovery_topic, discovery_payload in self._discovery_gen():
            payload_str = json.dumps(discovery_payload, separators=(",", ":"))
            logger.info(f"Publishing discovery: topic={discovery_topic} retained=True qos={QoS.AtLeastOnce.name} bytes={len(payload_str)}")
            logger.debug(f"Discovery payload: {payload_str}")
            discovery_infos.append(self._connection.publish(discovery_topic, payload_str, QoS.AtLeastOnce, True))

        # wait for all publish to finish
        for i in discovery_infos:
            i.wait_for_publish(publish_timeout)

    def _entities(self):
        for device in self._devices:
            for entity in device.entities:
                yield entity

    def homeassistant_status(self, connection, client, userdata, message: MQTTMessage):
        for entity in self._entities():
            if message.text == self.ha_status.payload_available:
                entity.home_assistant_birth(connection)
            elif message.text == self.ha_status.payload_not_available:
                entity.home_assistant_death(connection)
            else:
                logger.warning(f"Unknown Home Assistant status(topic={self._discovery_prefix}/status) message {message}")

    def run(self, schedule_resolution: float = 1.0, publish_timeout: float | None = None):
        if not self._connection.is_connected:
            self._connection.connect()

        self._discovery(publish_timeout)

        # Subscribe HA Status
        self._connection.subscribe(self.ha_status.topic, self.homeassistant_status)

        # register publishers with interval
        tasks = [schedule for entity in self._entities() for schedule in entity.schedules]
        Scheduler(*tasks).run_forever(schedule_resolution, self._connection)

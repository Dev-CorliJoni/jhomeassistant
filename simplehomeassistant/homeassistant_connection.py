from __future__ import annotations

import json
from typing import List, Any
from simplemqtt import QualityOfService as QoS
from simplemqtt.mqtt_connections import MqttConnectionBase, MQTTConnectionV3, MQTTConnectionV5

from simplehomeassistant.helper import validate_discovery_prefix
from simplehomeassistant.homeassistant_device import HomeAssistantDevice
from simplehomeassistant.types import AvailabilityMode


class HomeAssistantConnection:
    def __init__(self, connection: MqttConnectionBase):
        self._discovery_prefix = 'homeassistant'
        self._connection = connection
        self._devices: List[HomeAssistantDevice] = []
        self._availability_config: dict[str, Any] = {"availability": [{"topic": self._connection.availability_topic}]} \
            if self._connection.availability_topic else {}

    def discovery_prefix(self, discovery_prefix: str):
        self._discovery_prefix = validate_discovery_prefix(discovery_prefix)
        return self

    def add_devices(self, *devices: HomeAssistantDevice):
        for device in devices:
            self._devices.append(device)
        return self

    def deactivate_availability(self):
        self._availability_config = {}
        return self

    def customize_availability(self, availability_mode: AvailabilityMode = AvailabilityMode.LATEST, payload_online="online", payload_offline="offline", value_template=None):
        if "availability" in self._availability_config:
            if availability_mode != AvailabilityMode.LATEST:
                self._availability_config["availability_mode"] = availability_mode.value
            if payload_online != "online":
                self._availability_config["availability"][0]["payload_available"] = payload_online
            if payload_offline != "offline":
                self._availability_config["availability"][0]["payload_not_available"] = payload_offline
            if isinstance(value_template, str):
                self._availability_config["availability"][0]["value_template"] = value_template
        else:
            raise Exception("Cannot customize availability unless it was enabled with MQTTBuilder.availability(...) and hasn't been deactivated.")
        return self

    def run(self, publish_timeout=None):

        """if self._connection.is_connected:
            self._connection.connect()"""

        discovery_infos = []
        for device in self._devices:
            for discovery_topic, discovery_payload in device.discovery_gen(self._discovery_prefix):
                availability = {**self._availability_config}
                if "availability" in discovery_payload and isinstance(discovery_payload["availability"], list):
                    if "availability" not in availability:
                        availability["availability"] = []
                    availability["availability"].append(discovery_payload["availability"])

                discovery_payload = {**discovery_payload, **availability}

                if isinstance(self._connection, MQTTConnectionV3):
                    discovery_infos.append(self._connection.publish(discovery_topic, json.dumps(discovery_payload, separators=(",", ":")),  QoS.AtLeastOnce, True))

        # wait for discovery
        for i in discovery_infos:
            i.wait_for_publish(publish_timeout)


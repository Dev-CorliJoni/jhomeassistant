from __future__ import annotations

from typing import List

from jmqtt import QualityOfService as QoS

from jhomeassistant.features import Availability
from jhomeassistant.features.availability.availability_source import AvailabilitySource
from jhomeassistant.helper import validate_non_empty_string
from jhomeassistant.helper.abbreviations import OriginAbbreviation, Abbreviation
from jhomeassistant.homeassistant_device import HomeAssistantDevice
from jhomeassistant.setup_logging import get_logger

logger = get_logger("HomeAssistantOrigin")


class HomeAssistantOrigin:
    def __init__(self, name: str, sw_version: str | None = None, url: str | None = None):
        self.name = name
        self.sw_version = sw_version
        self.url = url
        self.availability = Availability(source=AvailabilitySource.ORIGIN)
        self.qos: QoS | None = None
        self.encoding: str | None = None
        self._devices: List[HomeAssistantDevice] = []

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str):
        self._name = validate_non_empty_string(value, "Origin 'name'")

    @property
    def sw_version(self) -> str | None:
        return self._sw_version

    @sw_version.setter
    def sw_version(self, value: str | None):
        self._sw_version = validate_non_empty_string(value, "Origin 'sw_version'", True)

    @property
    def url(self) -> str | None:
        return self._url

    @url.setter
    def url(self, value: str | None):
        self._url = validate_non_empty_string(value, "Origin 'url'", True)

    def add_devices(self, *devices: HomeAssistantDevice) -> HomeAssistantOrigin:
        for device in devices:
            self._devices.append(device)
        return self

    def _to_origin_dict(self) -> dict:
        result = {OriginAbbreviation.NAME: self._name}
        if self._sw_version:
            result[OriginAbbreviation.SW] = self._sw_version
        if self._url:
            result[OriginAbbreviation.URL] = self._url
        return {Abbreviation.ORIGIN: result}

    def _discovery_gen(self, discovery_prefix: str):
        for device in self._devices:
            if device.qos is None and self.qos is not None:
                device.qos = self.qos
                logger.info(f"Inherit origin QoS={self.qos.name} to device {device.name}")
            if device.encoding is None and self.encoding is not None:
                device.encoding = self.encoding
                logger.info(f"Inherit origin encoding={self.encoding} to device {device.name}")

            device.availability.internal_merge(self.availability)

            discovery_topic, discovery_payload = device.internal_discovery(discovery_prefix)
            discovery_payload = {**discovery_payload, **self._to_origin_dict()}
            yield discovery_topic, discovery_payload

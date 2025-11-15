from __future__ import annotations

from simplehomeassistant.helper import validate_non_empty_string
from simplehomeassistant.helper.abbreviations import OriginAbbreviation, Abbreviation


class Origin:
    def __init__(self):
        self.name = None
        self.sw_version = None
        self.url = None

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, name: str | None):
        self._name = validate_non_empty_string(name, "Origin 'name'", True)

    @property
    def sw_version(self):
        return self._sw_version

    @sw_version.setter
    def sw_version(self, sw_version: str | None):
        self._sw_version = validate_non_empty_string(sw_version, "Origin 'sw_version'", True)

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url: str | None):
        self._url = validate_non_empty_string(url, "Origin 'url'", True)

    def internal_to_dict(self):
        # Enforce required origin.name for device-based discovery
        if not isinstance(self.name, str) or self.name.strip() == "":
            raise ValueError(
                "origin.name is required for device-based discovery. "
                "Set HomeAssistantConnection.origin.name before discovery."
            )

        result = {
            OriginAbbreviation.NAME: self.name,
        }

        if self.sw_version:
            result[OriginAbbreviation.SW] = self.sw_version
        if self.url:
            result[OriginAbbreviation.URL] = self.url

        return {
            Abbreviation.ORIGIN: result
        }

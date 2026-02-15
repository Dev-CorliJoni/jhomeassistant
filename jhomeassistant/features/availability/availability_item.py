from __future__ import annotations

from jhomeassistant.features import TopicConfig
from jhomeassistant.helper import validate_non_empty_string
from jhomeassistant.helper.abbreviations import Abbreviation


class AvailabilityItem(TopicConfig):
    def __init__(self, topic: str, payload_available: str = TopicConfig.DEFAULT_AVAILABLE,
                 payload_not_available: str = TopicConfig.DEFAULT_NOT_AVAILABLE, value_template=None):
        super().__init__(topic, payload_available, payload_not_available)
        self.value_template = value_template

    @property
    def value_template(self):
        return self._value_template

    @value_template.setter
    def value_template(self, value_template: str | None):
        self._value_template = validate_non_empty_string(value_template, "Origin 'value_template'", True)

    def internal_to_dict(self):
        result = {Abbreviation.TOPIC: self.topic}

        if self.payload_available != TopicConfig.DEFAULT_AVAILABLE:
            result[Abbreviation.PAYLOAD_AVAILABLE] = self.payload_available
        if self.payload_not_available != TopicConfig.DEFAULT_NOT_AVAILABLE:
            result[Abbreviation.PAYLOAD_NOT_AVAILABLE] = self.payload_not_available
        if self.value_template is not None:
            result[Abbreviation.VALUE_TEMPLATE] = self.value_template

        return result

    def __repr__(self):
        return f"AvailabilityItem(topic={self.topic}, payload_available={self.payload_available}, payload_not_available={self.payload_not_available}, value_template={self.value_template})"

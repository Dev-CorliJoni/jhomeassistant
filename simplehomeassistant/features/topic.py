from __future__ import annotations

from simplehomeassistant.helper import validate_topic, validate_non_empty_string


class TopicConfig:
    DEFAULT_AVAILABLE = "online"
    DEFAULT_NOT_AVAILABLE = "offline"

    def __init__(self, topic: str, payload_available: str = DEFAULT_AVAILABLE, payload_not_available: str = DEFAULT_NOT_AVAILABLE):
        self.topic = validate_topic(topic)
        self.payload_available = payload_available
        self.payload_not_available = payload_not_available

    @property
    def topic(self):
        return self._topic

    @topic.setter
    def topic(self, topic: str):
        self._topic = validate_topic(topic)

    @property
    def payload_available(self):
        return self._payload_available

    @payload_available.setter
    def payload_available(self, payload_available: str):
        self._payload_available = validate_non_empty_string(payload_available, "TopicConfig 'payload_available'")

    @property
    def payload_not_available(self):
        return self._payload_not_available

    @payload_not_available.setter
    def payload_not_available(self, payload_not_available: str):
        self._payload_not_available = validate_non_empty_string(payload_not_available, "TopicConfig 'payload_not_available'")

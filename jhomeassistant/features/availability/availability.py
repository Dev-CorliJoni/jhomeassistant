from __future__ import annotations

from typing import Union, List

from ..topic import TopicConfig
from .availability_item import AvailabilityItem
from .availability_source import AvailabilitySource
from jhomeassistant.setup_logging import get_logger
from jhomeassistant.types import AvailabilityMode
from jhomeassistant.helper import validate_topic
from jhomeassistant.helper.abbreviations import Abbreviation


logger = get_logger("Availability")


class Availability:
    def __init__(self, source: AvailabilitySource, topic: str | None = None):
        self._source = source
        self._mode = None
        self._items: List[AvailabilityItem] = []
        if topic is not None:
            self.add(topic)

    def __getitem__(self, key: Union[int, str]):
        if isinstance(key, int):
            return self._items[key]
        return next((i for i in self._items if i.topic == key), None)

    def __iter__(self):
        return iter(self._items)

    def remove(self, topic: str):
        """Remove an availability source by topic."""
        item = self[topic]
        if item is None:
            raise KeyError(f"Topic {topic!r} not found.")
        self._items.remove(item)
        logger.info(f"Removed topic={topic!r}")
        return self

    def deactivate(self):
        """Deactivate all availability sources."""
        self._items = []
        return self

    def add(self, topic: str, payload_available: str = TopicConfig.DEFAULT_AVAILABLE,
            payload_not_available: str = TopicConfig.DEFAULT_NOT_AVAILABLE, value_template: str | None = None):
        """Add a new availability source."""
        validate_topic(topic)
        if any(i.topic == topic for i in self._items):
            raise ValueError(f"Availability for topic {topic!r} already exists. Modify it via Availability[{topic!r}] or Availability[index].")

        self._items.append(AvailabilityItem(topic, payload_available, payload_not_available, value_template, self._source))
        logger.info(f"Added availability topic={topic!r}.")
        return self

    @property
    def mode(self):
        return self._mode if self._mode is not None else AvailabilityMode.LATEST

    @mode.setter
    def mode(self, mode: AvailabilityMode):
        self._mode = mode

    @property
    def active(self):
        return len(self._items) > 0

    def internal_merge(self, other: Availability):
        """Merge availability from other into self. Idempotent: clears previously merged items before re-merging."""
        self._items = [i for i in self._items if i._source == self._source]
        for item in other:
            if self[item.topic] is None:
                self._items.append(item)
            else:
                logger.warning(f"Duplicate availability topic during merge. Preferring own availability item: {self[item.topic]!r}")

    def internal_to_dict(self):
        result = {}
        if len(self._items) > 0:
            result[Abbreviation.AVAILABILITY] = [i.internal_to_dict() for i in self._items]
        if self._mode is not None:
            result[Abbreviation.AVAILABILITY_MODE] = self._mode

        return result

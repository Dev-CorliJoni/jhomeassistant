from __future__ import annotations
from typing import Union

from jhomeassistant.entities.stateful_entity import StatefulEntity
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component
from jhomeassistant.types.device_classes import SensorDeviceClass
from jhomeassistant.types.entity_category import EntityCategory
from jhomeassistant.types.units.base import BaseUnit


class SensorEntity(StatefulEntity):
    """A sensor entity that publishes a value to its state_topic."""

    def __init__(self,
                 name: str,
                 state_topic: str,
                 device_class: SensorDeviceClass | None = None,
                 unit: BaseUnit | None = None,
                 value_template: str | None = None,
                 entity_category: EntityCategory | None = None) -> None:
        super().__init__(Component.SENSOR, name, state_topic=state_topic)
        self._device_class = device_class
        self._unit = unit
        self._value_template = value_template
        self._entity_category = entity_category

    def publish(self, value: Union[str, int, float]) -> None:
        self._get_connection().publish(self._state_topic, str(value))

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        if self._device_class is not None:
            payload[Abbreviation.DEVICE_CLASS] = self._device_class.value
        if self._unit is not None:
            payload[Abbreviation.UNIT_OF_MEASUREMENT] = self._unit.value
        if self._value_template is not None:
            payload[Abbreviation.VALUE_TEMPLATE] = self._value_template
        if self._entity_category is not None:
            payload[Abbreviation.ENTITY_CATEGORY] = self._entity_category.value
        return payload

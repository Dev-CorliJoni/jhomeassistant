from __future__ import annotations
from typing import Callable, List

from jmqtt import QualityOfService as QoS

from jhomeassistant.entities.commandable_entity import CommandableEntity
from jhomeassistant.entities.stateful_entity import StatefulEntity
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.types.component import Component
from jhomeassistant.types.entity_category import EntityCategory


class SelectEntity(StatefulEntity, CommandableEntity):
    """A select entity. HA renders a dropdown; selecting an option publishes to
    command_topic, and the current selection is published to state_topic.

    MRO: SelectEntity -> StatefulEntity -> CommandableEntity -> HomeAssistantEntityBase
    """

    def __init__(self,
                 name: str,
                 state_topic: str,
                 command_topic: str,
                 options: List[str],
                 on_select: Callable,
                 entity_category: EntityCategory | None = None,
                 retain: bool | None = None,
                 optimistic: bool | None = None,
                 value_template: str | None = None,
                 command_template: str | None = None) -> None:
        if not options:
            raise ValueError("SelectEntity 'options' must be a non-empty list")
        super().__init__(Component.SELECT, name,
                         state_topic=state_topic,
                         command_topic=command_topic,
                         on_command=on_select)
        self._options: List[str] = list(options)
        self._entity_category = entity_category
        self._retain = retain
        self._optimistic = optimistic
        self._value_template = value_template
        self._command_template = command_template

    def publish(
        self,
        option: str,
        qos: QoS = QoS.AtMostOnce,
        retain: bool = False,
        wait_for_publish: bool = False,
    ) -> None:
        if option not in self._options:
            raise ValueError(f"Option '{option}' not in options: {self._options}")
        self._publish_state(option, qos, retain, wait_for_publish)

    @property
    def internal_discovery_payload(self) -> dict:
        payload = super().internal_discovery_payload
        payload[Abbreviation.OPTIONS] = self._options
        if self._entity_category is not None:
            payload[Abbreviation.ENTITY_CATEGORY] = self._entity_category.value
        if self._retain is not None:
            payload[Abbreviation.RETAIN] = self._retain
        if self._optimistic is not None:
            payload[Abbreviation.OPTIMISTIC] = self._optimistic
        if self._value_template is not None:
            payload[Abbreviation.VALUE_TEMPLATE] = self._value_template
        if self._command_template is not None:
            payload[Abbreviation.COMMAND_TEMPLATE] = self._command_template
        return payload

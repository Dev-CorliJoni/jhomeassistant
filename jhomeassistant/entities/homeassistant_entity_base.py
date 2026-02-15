from __future__ import annotations
from typing import Callable, Union, List

from jmqtt import MQTTConnectionV3, MQTTConnectionV5, client_identity

from jhomeassistant.features import Availability
from jhomeassistant.helper import validate_non_empty_string
from jhomeassistant.helper.abbreviations import Abbreviation
from jhomeassistant.helper.scheduler import Schedule
from jhomeassistant.types.component import Component


class HomeAssistantEntityBase:
    def __init__(self, component: Component, name):
        validate_non_empty_string(name, "Entity 'name'")
        self._schedules: List[Schedule] = []
        self._name = name
        self._component = component

        self.availability = Availability()

    def add_schedule(self, interval: float, function: Callable[[Union[MQTTConnectionV3, MQTTConnectionV5]], None]):
        self._schedules.append(Schedule(interval, function))
        return self

    @property
    def schedules(self):
        return self._schedules

    @property
    def identifier(self):
        return client_identity.hashing.build_urlsafe_token(self._name)

    @property
    def name(self):
        return self._name

    @property
    def platform(self):
        return self._component

    @property
    def internal_discovery_payload(self):
        return {
            "component": self._component.value,
            Abbreviation.NAME: self._name,
            **self.availability.internal_to_dict()
        }

    def home_assistant_birth(self, connection: Union[MQTTConnectionV3, MQTTConnectionV5]):
        pass

    def home_assistant_death(self, connection: Union[MQTTConnectionV3, MQTTConnectionV5]):
        pass

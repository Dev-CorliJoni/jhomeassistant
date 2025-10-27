from __future__ import annotations
from simplehomeassistant.helper import validate_node_id, validate_object_id, validate_component



class HomeAssistantEntityBase:
    def __init__(self, component, object_id):
        self._component = validate_component(component)
        self._node_id = None
        self._object_id = validate_object_id(object_id)

    @property
    def has_node_id(self):
        return self._node_id is not None

    def node_id(self, node_id: str | None) -> HomeAssistantEntityBase:
        self._node_id = validate_node_id(node_id)
        return self

    def object_id(self, object_id: str) -> HomeAssistantEntityBase:
        self._object_id = validate_node_id(object_id)
        return self

    def _get_relative_identity(self, seperator: str):
        node_id = f"{self._node_id}{seperator}" if self.has_node_id else ""
        return f"{self._component}{seperator}{node_id}{self._object_id}"

    @property
    def relative_unique_id(self) -> str:
        return self._get_relative_identity("-")

    @property
    def relative_discovery_prefix(self):
        return f"{self._get_relative_identity('/')}/config"

    @property
    def discovery_payload(self):
        return {

        }

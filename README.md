# jhomeassistant

A Python library for Home Assistant MQTT device discovery based on `jmqtt` connections.

## Installation

```bash
pip install jhomeassistant
```

## Requirements

- Python `>=3.8`
- `jmqtt`
- `python-slugify`

## Quickstart

```python
from jmqtt import MQTTBuilderV3
from jhomeassistant import HomeAssistantConnection, HomeAssistantDevice
from jhomeassistant.entities import HomeAssistantEntityBase
from jhomeassistant.types import Component

# 1) Build MQTT connection
connection = (
    MQTTBuilderV3(host="localhost", app_name="my-tool")
    .instance_id("main")
    .availability("my-tool/status")
    .fast_build()
)

# 2) Wrap it for Home Assistant discovery
ha = HomeAssistantConnection(connection)
ha.origin.name = "my-tool"

# 3) Define an entity by subclassing HomeAssistantEntityBase
class TemperatureEntity(HomeAssistantEntityBase):
    def __init__(self):
        super().__init__(Component.SENSOR, "Temperature")

entity = TemperatureEntity()
device = HomeAssistantDevice("Kitchen Sensor").add_entities(entity)

# 4) Register and run discovery + scheduler loop
ha.add_devices(device)
ha.run()
```

## Core Concepts

### `HomeAssistantConnection`

- Holds a `jmqtt` connection (`MQTTConnectionV3` or `MQTTConnectionV5`)
- Builds and publishes Home Assistant device discovery payloads
- Subscribes to `homeassistant/status` and dispatches birth/death hooks to entities

Main configuration:

- `discovery_prefix("homeassistant")`
- `origin.name`, `origin.sw_version`, `origin.url`
- `availability` (connection-level availability inheritance)
- `qos`, `encoding` (connection-level defaults inherited by devices)

### `HomeAssistantDevice`

- Represents one Home Assistant device block in discovery
- Auto-detects runtime device facts using `jmqtt.client_identity.facts`
- Derives stable identifiers for discovery and entity unique IDs
- Supports `prevent_device_merge=True` to avoid connection-based merge identifiers

Common fields:

- `manufacturer`, `model`, `model_id`
- `hw_version`, `sw_version`
- `via_device`, `configuration_url`
- `qos`, `encoding`
- `availability`

### `HomeAssistantEntityBase`

- Base class for entities that belong to a `HomeAssistantDevice`
- Provides deterministic `identifier` and discovery payload base
- Supports scheduled publisher functions via `add_schedule(interval, function)`
- Lifecycle hooks:
  - `home_assistant_birth(connection)`
  - `home_assistant_death(connection)`

## Discovery Output

`HomeAssistantConnection.discovery_text()` returns formatted discovery topics + payloads,
useful for debugging and tests.

## Notes

- `origin.name` is required by device-based discovery payload validation.
- If not set explicitly, device name is used as fallback.
- Entity names should be unique within a device to avoid unique_id collisions.

## License

MIT (see `LICENSE`).

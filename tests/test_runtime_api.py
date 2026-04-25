from __future__ import annotations

import threading
import time

import jhomeassistant.homeassistant_device as homeassistant_device_module
from jhomeassistant import HomeAssistantConnection, HomeAssistantDevice, HomeAssistantOrigin
from jhomeassistant.entities import ButtonEntity, HomeAssistantEntityBase
from jhomeassistant.types import Component


class _FakePublishInfo:
    def __init__(self):
        self.publish_timeouts = []

    def wait_for_publish(self, timeout: float | None = None):
        self.publish_timeouts.append(timeout)


class _FakeMqttConnection:
    def __init__(self):
        self.availability_topic = None
        self.is_connected = False

        self.connect_calls = 0
        self.publish_calls = []
        self.subscribe_calls = []
        self.unsubscribe_calls = []
        self.raise_on_publish: Exception | None = None
        self._on_connect_callbacks = []

    def add_on_connect(self, cb):
        self._on_connect_callbacks.append(cb)

    def connect(self):
        self.connect_calls += 1
        self.is_connected = True
        for cb in self._on_connect_callbacks:
            cb(self, None, None, 0)
        return self

    def publish(self, topic, payload, qos, retain):
        if self.raise_on_publish is not None:
            raise self.raise_on_publish

        info = _FakePublishInfo()
        self.publish_calls.append((topic, payload, qos, retain, info))
        return info

    def subscribe(self, topic, callback):
        self.subscribe_calls.append((topic, callback))
        return 0, len(self.subscribe_calls)

    def unsubscribe(self, *topics):
        self.unsubscribe_calls.extend(topics)


def _build_connection(mqtt_connection: _FakeMqttConnection) -> tuple[HomeAssistantConnection, threading.Event]:
    schedule_event = threading.Event()

    entity = HomeAssistantEntityBase(Component.SENSOR, "Temperature")
    entity.add_schedule(0.01, lambda _conn: schedule_event.set())

    device = HomeAssistantDevice("Runtime Device").add_entities(entity)
    origin = HomeAssistantOrigin("Runtime App").add_devices(device)
    connection = HomeAssistantConnection(mqtt_connection).add_origin(origin)
    return connection, schedule_event


def test_runtime_non_blocking_start_stop_and_restart(monkeypatch):
    monkeypatch.setattr(
        homeassistant_device_module.client_identity.facts,
        "collect_device_facts",
        lambda: ("serial-runtime", []),
    )

    mqtt_connection = _FakeMqttConnection()
    connection, schedule_event = _build_connection(mqtt_connection)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert schedule_event.wait(timeout=1.0)
    assert runtime.is_running is True

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True
    assert runtime.is_running is False
    assert runtime.last_error is None
    assert mqtt_connection.connect_calls == 1
    assert len(mqtt_connection.publish_calls) == 1
    assert len(mqtt_connection.subscribe_calls) == 1
    assert mqtt_connection.unsubscribe_calls.count("homeassistant/status") == 1

    schedule_event.clear()
    runtime2 = connection.run(blocking=False, schedule_resolution=0.01)
    assert runtime2 is not None
    assert schedule_event.wait(timeout=1.0)
    runtime2.stop(timeout=1.0)
    assert runtime2.join(timeout=1.0) is True

    assert len(mqtt_connection.publish_calls) == 2
    assert len(mqtt_connection.subscribe_calls) == 2
    assert mqtt_connection.unsubscribe_calls.count("homeassistant/status") == 2


def test_runtime_start_is_idempotent(monkeypatch):
    monkeypatch.setattr(
        homeassistant_device_module.client_identity.facts,
        "collect_device_facts",
        lambda: ("serial-runtime", []),
    )

    mqtt_connection = _FakeMqttConnection()
    connection, _ = _build_connection(mqtt_connection)

    runtime1 = connection.run(blocking=False, schedule_resolution=0.01)
    runtime2 = connection.run(blocking=False, schedule_resolution=0.01)
    assert runtime1 is runtime2

    time.sleep(0.05)
    assert len(mqtt_connection.publish_calls) == 1
    assert len(mqtt_connection.subscribe_calls) == 1

    runtime1.stop(timeout=1.0)
    assert runtime1.join(timeout=1.0) is True


def test_runtime_captures_background_errors(monkeypatch):
    monkeypatch.setattr(
        homeassistant_device_module.client_identity.facts,
        "collect_device_facts",
        lambda: ("serial-runtime", []),
    )

    mqtt_connection = _FakeMqttConnection()
    mqtt_connection.raise_on_publish = RuntimeError("discovery failed")
    connection, _ = _build_connection(mqtt_connection)

    runtime = connection.run(blocking=False)
    assert runtime is not None
    assert runtime.join(timeout=1.0) is True
    assert isinstance(runtime.last_error, RuntimeError)
    assert runtime.is_running is False

    runtime.stop(timeout=0.1)
    assert runtime.join(timeout=0.1) is True


def test_blocking_run_still_blocks_until_stopped(monkeypatch):
    monkeypatch.setattr(
        homeassistant_device_module.client_identity.facts,
        "collect_device_facts",
        lambda: ("serial-runtime", []),
    )

    mqtt_connection = _FakeMqttConnection()
    connection, schedule_event = _build_connection(mqtt_connection)

    blocking_thread = threading.Thread(
        target=connection.run,
        kwargs={"schedule_resolution": 0.01},
        daemon=True,
    )
    blocking_thread.start()

    assert schedule_event.wait(timeout=1.0)

    runtime = connection.run(blocking=False)
    assert runtime is not None
    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True

    blocking_thread.join(timeout=1.0)
    assert blocking_thread.is_alive() is False


def _patch_device_facts(monkeypatch):
    monkeypatch.setattr(
        homeassistant_device_module.client_identity.facts,
        "collect_device_facts",
        lambda: ("serial-runtime", []),
    )


def _build_full_tree(mqtt_connection: _FakeMqttConnection):
    """Connection with one origin, one device, and a ButtonEntity (subscribes to a command topic)."""
    button_presses = []
    button = ButtonEntity("Press Me", "test/cmd", on_press=lambda *_a: button_presses.append(True))

    device = HomeAssistantDevice("Runtime Device").add_entities(button)
    origin = HomeAssistantOrigin("Runtime App").add_devices(device)
    connection = HomeAssistantConnection(mqtt_connection).add_origin(origin)
    return connection, origin, device, button


def _device_topic(device: HomeAssistantDevice) -> str:
    return f"homeassistant/device/{device.unique_id}/config"


def test_remove_unknown_targets_are_noops(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    other_origin = HomeAssistantOrigin("Other")
    other_device = HomeAssistantDevice("Other Device")
    other_entity = HomeAssistantEntityBase(Component.SENSOR, "Detached")

    connection.remove_origin(other_origin)
    connection.remove_device(other_device)
    connection.remove_entity(other_entity)

    assert mqtt.publish_calls == []
    assert mqtt.unsubscribe_calls == []
    assert origin in connection._origins
    assert device in origin._devices


def test_remove_entity_unsubscribes_and_republishes(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, _origin, device, button = _build_full_tree(mqtt)

    connection.remove_entity(button)

    assert button not in device._entities
    assert "test/cmd" in mqtt.unsubscribe_calls
    # remove_entity republishes the parent device's discovery (non-empty payload).
    device_topic = _device_topic(device)
    republishes = [c for c in mqtt.publish_calls if c[0] == device_topic]
    assert len(republishes) == 1
    topic, payload, _qos, retain, _info = republishes[0]
    assert retain is True
    assert isinstance(payload, str) and payload != ""


def test_remove_device_publishes_empty_retained(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, button = _build_full_tree(mqtt)

    connection.remove_device(device)

    assert device not in origin._devices
    assert "test/cmd" in mqtt.unsubscribe_calls

    device_topic = _device_topic(device)
    deletes = [c for c in mqtt.publish_calls if c[0] == device_topic]
    assert len(deletes) == 1
    _topic, payload, _qos, retain, _info = deletes[0]
    assert payload == ""
    assert retain is True


def test_remove_origin_clears_each_device(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)
    second_device = HomeAssistantDevice("Second", identifier="second-id")
    origin.add_devices(second_device)

    connection.remove_origin(origin)

    assert origin not in connection._origins

    expected_topics = {_device_topic(device), _device_topic(second_device)}
    deletes = {c[0]: c for c in mqtt.publish_calls if c[1] == ""}
    assert set(deletes.keys()) == expected_topics
    for _topic, payload, _qos, retain, _info in deletes.values():
        assert payload == ""
        assert retain is True


def test_remove_is_idempotent(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, button = _build_full_tree(mqtt)

    connection.remove_entity(button)
    publishes_after_first = len(mqtt.publish_calls)
    unsubs_after_first = len(mqtt.unsubscribe_calls)

    connection.remove_entity(button)
    connection.remove_device(device)
    publishes_after_device = len(mqtt.publish_calls)

    connection.remove_device(device)
    connection.remove_origin(origin)
    publishes_after_origin = len(mqtt.publish_calls)

    connection.remove_origin(origin)

    assert publishes_after_first == 1  # republish of device
    assert publishes_after_device == publishes_after_first + 1  # device delete
    assert publishes_after_origin == publishes_after_device  # origin already empty
    assert len(mqtt.publish_calls) == publishes_after_origin
    assert len(mqtt.unsubscribe_calls) == unsubs_after_first  # button only unsubscribed once


def test_remove_entity_during_runtime_stops_scheduler_task(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()

    schedule_event = threading.Event()
    tick_count = {"n": 0}

    def _on_tick(_conn):
        tick_count["n"] += 1
        schedule_event.set()

    entity = HomeAssistantEntityBase(Component.SENSOR, "Temperature")
    entity.add_schedule(0.01, _on_tick)

    device = HomeAssistantDevice("Runtime Device").add_entities(entity)
    origin = HomeAssistantOrigin("Runtime App").add_devices(device)
    connection = HomeAssistantConnection(mqtt).add_origin(origin)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert schedule_event.wait(timeout=1.0)

    connection.remove_entity(entity)
    ticks_at_removal = tick_count["n"]
    time.sleep(0.05)
    # Scheduler should not fire the removed entity's task again.
    assert tick_count["n"] - ticks_at_removal <= 1

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_remove_origin_during_runtime(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    # Wait until on_connect has fired so subscribe(command_topic) ran.
    deadline = time.time() + 1.0
    while time.time() < deadline:
        if any(c[0] == "test/cmd" for c in mqtt.subscribe_calls):
            break
        time.sleep(0.01)
    assert any(c[0] == "test/cmd" for c in mqtt.subscribe_calls)

    connection.remove_origin(origin)

    assert "test/cmd" in mqtt.unsubscribe_calls
    device_topic = _device_topic(device)
    deletes = [c for c in mqtt.publish_calls if c[0] == device_topic and c[1] == ""]
    assert len(deletes) == 1

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


# ---------------------------------------------------------------------------
# add_entity / add_device / add_origin (dynamic add during runtime)
# ---------------------------------------------------------------------------

def _wait_for_subscribe(mqtt: _FakeMqttConnection, topic: str, timeout: float = 1.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if any(c[0] == topic for c in mqtt.subscribe_calls):
            return True
        time.sleep(0.01)
    return False


def test_add_entity_before_runtime_is_noop_then_activates_on_run(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    new_button = ButtonEntity("Late Button", "test/late_cmd", on_press=lambda *_: None)
    # add before run() — no subscribes yet
    connection.add_entity(new_button, device)
    assert new_button in device._entities
    assert not any(c[0] == "test/late_cmd" for c in mqtt.subscribe_calls)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert _wait_for_subscribe(mqtt, "test/late_cmd")

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_entity_during_runtime_subscribes_and_republishes(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert _wait_for_subscribe(mqtt, "test/cmd")

    publishes_before = len(mqtt.publish_calls)
    new_button = ButtonEntity("Late Button", "test/late_cmd", on_press=lambda *_: None)
    connection.add_entity(new_button, device)

    assert _wait_for_subscribe(mqtt, "test/late_cmd")
    # discovery must have been republished for the device
    device_topic = _device_topic(device)
    new_publishes = [c for c in mqtt.publish_calls[publishes_before:] if c[0] == device_topic and c[1] != ""]
    assert len(new_publishes) >= 1

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_entity_during_runtime_registers_schedule(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert _wait_for_subscribe(mqtt, "test/cmd")

    tick_event = threading.Event()
    sensor = HomeAssistantEntityBase(Component.SENSOR, "Late Sensor")
    sensor.add_schedule(0.01, lambda _conn: tick_event.set())
    connection.add_entity(sensor, device)

    assert tick_event.wait(timeout=1.0), "schedule of dynamically added entity never fired"

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_entity_is_idempotent(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, button = _build_full_tree(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert _wait_for_subscribe(mqtt, "test/cmd")

    publishes_before = len(mqtt.publish_calls)
    connection.add_entity(button, device)  # already present
    time.sleep(0.05)
    # no extra subscribe, only one extra republish (idempotent: entity not re-added)
    late_subs = [c for c in mqtt.subscribe_calls if c[0] == "test/cmd"]
    assert len(late_subs) == 1  # subscribed once during run(), not again

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_entity_unknown_device_is_noop(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, _origin, _device, _button = _build_full_tree(mqtt)

    orphan_device = HomeAssistantDevice("Orphan", identifier="orphan-id")
    new_entity = HomeAssistantEntityBase(Component.SENSOR, "Orphan Sensor")
    connection.add_entity(new_entity, orphan_device)  # device not registered

    assert new_entity not in orphan_device._entities
    assert mqtt.publish_calls == []


def test_add_device_during_runtime_subscribes_and_publishes_discovery(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, _device, _button = _build_full_tree(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    assert _wait_for_subscribe(mqtt, "test/cmd")

    new_button = ButtonEntity("New Button", "test/new_cmd", on_press=lambda *_: None)
    new_device = HomeAssistantDevice("New Device", identifier="new-device-id").add_entities(new_button)

    publishes_before = len(mqtt.publish_calls)
    connection.add_device(new_device, origin)

    assert _wait_for_subscribe(mqtt, "test/new_cmd")
    new_device_topic = _device_topic(new_device)
    new_publishes = [c for c in mqtt.publish_calls[publishes_before:] if c[0] == new_device_topic and c[1] != ""]
    assert len(new_publishes) >= 1

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_device_is_idempotent(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, device, _button = _build_full_tree(mqtt)

    connection.add_device(device, origin)  # already present — must not duplicate

    assert origin._devices.count(device) == 1
    assert mqtt.publish_calls == []


def test_add_device_unknown_origin_is_noop(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, _origin, _device, _button = _build_full_tree(mqtt)

    orphan_origin = HomeAssistantOrigin("Orphan")
    new_device = HomeAssistantDevice("New", identifier="new-id")
    connection.add_device(new_device, orphan_origin)

    assert new_device not in orphan_origin._devices
    assert mqtt.publish_calls == []


def test_add_origin_during_runtime_subscribes_and_publishes_discovery(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()

    # Start with an empty connection (no origins)
    connection = HomeAssistantConnection(mqtt)
    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    time.sleep(0.05)

    new_button = ButtonEntity("Late Button", "test/late_cmd", on_press=lambda *_: None)
    new_device = HomeAssistantDevice("Late Device", identifier="late-device-id").add_entities(new_button)
    new_origin = HomeAssistantOrigin("Late Origin").add_devices(new_device)

    publishes_before = len(mqtt.publish_calls)
    connection.add_origin(new_origin)

    assert _wait_for_subscribe(mqtt, "test/late_cmd")
    device_topic = _device_topic(new_device)
    new_publishes = [c for c in mqtt.publish_calls[publishes_before:] if c[0] == device_topic and c[1] != ""]
    assert len(new_publishes) >= 1
    assert new_origin in connection._origins

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True


def test_add_origin_is_idempotent(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection, origin, _device, _button = _build_full_tree(mqtt)

    connection.add_origin(origin)  # already present

    assert connection._origins.count(origin) == 1
    assert mqtt.publish_calls == []


def test_add_origin_during_runtime_registers_schedule(monkeypatch):
    _patch_device_facts(monkeypatch)
    mqtt = _FakeMqttConnection()
    connection = HomeAssistantConnection(mqtt)

    runtime = connection.run(blocking=False, schedule_resolution=0.01, publish_timeout=1.0)
    assert runtime is not None
    time.sleep(0.05)

    tick_event = threading.Event()
    sensor = HomeAssistantEntityBase(Component.SENSOR, "Late Sensor")
    sensor.add_schedule(0.01, lambda _conn: tick_event.set())
    late_device = HomeAssistantDevice("Late Device", identifier="late-sched-id").add_entities(sensor)
    late_origin = HomeAssistantOrigin("Late Origin").add_devices(late_device)
    connection.add_origin(late_origin)

    assert tick_event.wait(timeout=1.0), "schedule of dynamically added origin's entity never fired"

    runtime.stop(timeout=1.0)
    assert runtime.join(timeout=1.0) is True

from __future__ import annotations

import threading
import time

import jhomeassistant.homeassistant_device as homeassistant_device_module
from jhomeassistant import HomeAssistantConnection, HomeAssistantDevice
from jhomeassistant.entities import HomeAssistantEntityBase
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

    def connect(self):
        self.connect_calls += 1
        self.is_connected = True
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
    connection = HomeAssistantConnection(mqtt_connection).add_devices(device)
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

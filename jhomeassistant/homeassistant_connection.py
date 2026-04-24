from __future__ import annotations

import json
import threading
from typing import List, Union
from jmqtt import QualityOfService as QoS, MQTTMessage, MQTTConnectionV3, MQTTConnectionV5

from jhomeassistant.features import Availability, TopicConfig
from jhomeassistant.features.availability.availability_source import AvailabilitySource
from jhomeassistant.helper import validate_discovery_prefix
from jhomeassistant.helper.abbreviations import resolve_abbreviation
from jhomeassistant.entities import HomeAssistantEntityBase
from jhomeassistant.helper.scheduler import Scheduler
from jhomeassistant.homeassistant_device import HomeAssistantDevice
from jhomeassistant.homeassistant_origin import HomeAssistantOrigin
from jhomeassistant.homeassistant_runtime import HomeAssistantRuntime
from jhomeassistant.homeassistant_runtime_record import _RuntimeRecord
from jhomeassistant.setup_logging import get_logger


logger = get_logger("HomeAssistantConnection")

_RUNTIME_IDLE = "idle"
_RUNTIME_RUNNING = "running"
_RUNTIME_STOPPING = "stopping"
_RUNTIME_STOPPED = "stopped"
_RUNTIME_ACTIVE_STATES = {_RUNTIME_RUNNING, _RUNTIME_STOPPING}


def resolve_abbreviations(payload: dict, use_abbreviated_device_discovery: bool) -> dict:
    new_payload = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            value = resolve_abbreviations(value, use_abbreviated_device_discovery)

        elif isinstance(value, list):
            normalized_list = []
            for item in value:
                if isinstance(item, dict):
                    normalized_list.append(
                        resolve_abbreviations(item, use_abbreviated_device_discovery)
                    )
                else:
                    normalized_list.append(item)
            value = normalized_list

        if not isinstance(key, str):
            key = resolve_abbreviation(key, use_abbreviated_device_discovery)

        new_payload[key] = value
    return new_payload

class HomeAssistantConnection:
    def __init__(self, connection: Union[MQTTConnectionV3, MQTTConnectionV5], use_abbreviated_device_discovery=False):
        self._use_abbreviated_device_discovery = use_abbreviated_device_discovery
        self._connection = connection
        self._origins: List[HomeAssistantOrigin] = []
        self._discovery_prefix = 'homeassistant'

        self.availability = Availability(AvailabilitySource.CONNECTION, self._connection.availability_topic)
        self.ha_status = TopicConfig("homeassistant/status")
        self.qos: QoS | None = None
        self.encoding: str | None = None

        self._runtime_lock = threading.RLock()
        self._runtime: _RuntimeRecord | None = None
        self._scheduler: Scheduler | None = None

    def get_connection(self) -> Union[MQTTConnectionV3, MQTTConnectionV5]:
        """Returns the active MQTT connection. Passed to entities and the scheduler.
        Raises RuntimeError if mqtt_connected() has not been called on the entity yet."""
        if self._connection is None:
            raise RuntimeError(
                "No MQTT connection available. "
                "Ensure HomeAssistantConnection was initialized with a valid connection."
            )
        return self._connection

    def discovery_prefix(self, discovery_prefix: str) -> HomeAssistantConnection:
        self._discovery_prefix = validate_discovery_prefix(discovery_prefix)
        return self

    def add_origin(self, *origins: HomeAssistantOrigin) -> HomeAssistantConnection:
        for origin in origins:
            self._origins.append(origin)
        return self

    def _discovery_gen(self):
        for origin in self._origins:
            if origin.qos is None and self.qos is not None:
                origin.qos = self.qos
                logger.info(f"Inherit connection QoS={self.qos.name} to origin {origin.name}")
            if origin.encoding is None and self.encoding is not None:
                origin.encoding = self.encoding
                logger.info(f"Inherit connection encoding={self.encoding} to origin {origin.name}")

            origin.availability.internal_merge(self.availability)

            for discovery_topic, discovery_payload in origin._discovery_gen(self._discovery_prefix):
                yield discovery_topic, resolve_abbreviations(discovery_payload, self._use_abbreviated_device_discovery)

    def discovery_text(self):
        text = ""
        for topic, payload in self._discovery_gen():
            pretty = json.dumps(
                payload,
                indent=2,
                sort_keys=True,
                ensure_ascii=False,
            )
            text += f"-------------------------- Topic: {topic} --------------------------\n{pretty}\n\n"
        return text

    def _discovery(self, publish_timeout):
        """Publish all discovery payloads and wait for completion."""
        discovery_infos = []
        for discovery_topic, discovery_payload in self._discovery_gen():
            payload_str = json.dumps(discovery_payload, separators=(",", ":"))
            logger.info(f"Publishing discovery: topic={discovery_topic} retained=True qos={QoS.AtLeastOnce.name} bytes={len(payload_str)}")
            logger.debug(f"Discovery payload: {payload_str}")
            discovery_infos.append(self._connection.publish(discovery_topic, payload_str, QoS.AtLeastOnce, True))

        for i in discovery_infos:
            i.wait_for_publish(publish_timeout)

    def _entities(self):
        for origin in self._origins:
            for device in origin._devices:
                for entity in device.entities:
                    yield entity

    def homeassistant_status(self, connection, client, userdata, message: MQTTMessage):
        for entity in self._entities():
            if message.text == self.ha_status.payload_available:
                entity.home_assistant_birth(connection)
            elif message.text == self.ha_status.payload_not_available:
                entity.home_assistant_death(connection)
            else:
                logger.warning(f"Unknown Home Assistant status(topic={self._discovery_prefix}/status) message {message}")

    def _runtime_cleanup(self, runtime: _RuntimeRecord) -> None:
        runtime.stop_event.set()

        try:
            self._connection.unsubscribe(self.ha_status.topic)
        except Exception as exc:
            logger.debug(f"Failed to unsubscribe Home Assistant status topic ({self.ha_status.topic}): {exc}")

        with self._runtime_lock:
            runtime.state = _RUNTIME_STOPPED
            runtime.done_event.set()
            if self._runtime is runtime:
                self._runtime = None
            self._scheduler = None

    def _runtime_execute(self, runtime: _RuntimeRecord, schedule_resolution: float, publish_timeout: float | None, re_raise_errors: bool) -> None:
        with self._runtime_lock:
            runtime.owner_thread_id = threading.get_ident()

        try:
            def on_mqtt_connect(*_args):
                for entity in self._entities():
                    entity.mqtt_connected(self.get_connection)

            self._connection.add_on_connect(on_mqtt_connect)

            if not self._connection.is_connected:
                # on_mqtt_connect will be triggered via the registered add_on_connect hook
                self._connection.connect()
            else:
                for entity in self._entities():
                    entity.mqtt_connected(self.get_connection)

            self._discovery(publish_timeout)
            self._connection.subscribe(self.ha_status.topic, self.homeassistant_status)

            tasks = [schedule for entity in self._entities() for schedule in entity.schedules]
            scheduler = Scheduler(*tasks)
            with self._runtime_lock:
                self._scheduler = scheduler
            scheduler.run_forever(
                schedule_resolution,
                self.get_connection,
                stop_event=runtime.stop_event,
            )
        except Exception as exc:
            with self._runtime_lock:
                runtime.last_error = exc
            logger.exception(f"Home Assistant runtime failed: {exc}")
            if re_raise_errors:
                raise
        finally:
            self._runtime_cleanup(runtime)

    def _runtime_stop(self, runtime: _RuntimeRecord, timeout: float | None = None) -> None:
        with self._runtime_lock:
            if runtime.state in {_RUNTIME_IDLE, _RUNTIME_STOPPED}:
                return
            if runtime.state == _RUNTIME_RUNNING:
                runtime.state = _RUNTIME_STOPPING
            runtime.stop_event.set()

        if timeout is not None:
            self._runtime_join(runtime, timeout)

    def _runtime_join(self, runtime: _RuntimeRecord, timeout: float | None = None) -> bool:
        return runtime.done_event.wait(timeout)

    def _runtime_is_running(self, runtime: _RuntimeRecord) -> bool:
        with self._runtime_lock:
            return self._runtime_is_active_unlocked(runtime)

    def _runtime_last_error(self, runtime: _RuntimeRecord) -> Exception | None:
        with self._runtime_lock:
            return runtime.last_error

    def run(self, schedule_resolution: float = 1.0, publish_timeout: float | None = None, blocking: bool = True) -> HomeAssistantRuntime | None:
        thread_to_start = None
        create_new_runtime = False

        with self._runtime_lock:
            runtime = self._runtime
            if runtime is not None and self._runtime_is_active_unlocked(runtime):
                handle = self._runtime_handle_unlocked(runtime)
            else:
                runtime = _RuntimeRecord(_RUNTIME_RUNNING)
                handle = self._runtime_handle_unlocked(runtime)
                self._runtime = runtime
                create_new_runtime = True

                if not blocking:
                    thread = threading.Thread(
                        target=self._runtime_execute,
                        kwargs={
                            "runtime": runtime,
                            "schedule_resolution": schedule_resolution,
                            "publish_timeout": publish_timeout,
                            "re_raise_errors": False,
                        },
                        name="jhomeassistant-runtime",
                        daemon=True,
                    )
                    runtime.thread = thread
                    thread_to_start = thread

        if not create_new_runtime:
            if blocking:
                with self._runtime_lock:
                    owner_thread_id = runtime.owner_thread_id
                if owner_thread_id == threading.get_ident():
                    logger.warning("Home Assistant runtime is already running in the current thread.")
                    return None

                handle.join()
                if handle.last_error is not None:
                    raise handle.last_error
                return None
            return handle

        if thread_to_start is not None:
            thread_to_start.start()
            return handle

        self._runtime_execute(runtime, schedule_resolution, publish_timeout, re_raise_errors=True)
        return None

    def _runtime_is_active_unlocked(self, runtime: _RuntimeRecord) -> bool:
        return runtime.state in _RUNTIME_ACTIVE_STATES and not runtime.done_event.is_set()

    def _runtime_handle_unlocked(self, runtime: _RuntimeRecord) -> HomeAssistantRuntime:
        if runtime.handle is None:
            runtime.handle = HomeAssistantRuntime(self, runtime)
        return runtime.handle

    def runtime(self) -> HomeAssistantRuntime | None:
        with self._runtime_lock:
            if self._runtime is None:
                return None
            if not self._runtime_is_active_unlocked(self._runtime):
                return None
            return self._runtime_handle_unlocked(self._runtime)

    def republish_discovery(self, publish_timeout: float | None = None) -> None:
        self._discovery(publish_timeout)

    def _cleanup_entity_runtime(self, entity: HomeAssistantEntityBase) -> None:
        """Release runtime resources held by the entity (subscriptions, scheduled tasks). Idempotent."""
        try:
            entity.cleanup(self._connection)
        except Exception as exc:
            logger.debug(f"Entity cleanup failed for {entity.name!r}: {exc}")

        scheduler = self._scheduler
        if scheduler is not None and entity.schedules:
            try:
                scheduler.remove_tasks(*entity.schedules)
            except Exception as exc:
                logger.debug(f"Failed to remove scheduler tasks for entity {entity.name!r}: {exc}")

    def _publish_device_delete(self, device: HomeAssistantDevice, publish_timeout: float | None) -> None:
        """Publish empty retained payload to delete the device from Home Assistant."""
        topic = f"{self._discovery_prefix}/device/{device.unique_id}/config"
        try:
            logger.info(f"Publishing device-delete: topic={topic} retained=True qos={QoS.AtLeastOnce.name}")
            info = self._connection.publish(topic, "", QoS.AtLeastOnce, True)
            if publish_timeout is not None:
                info.wait_for_publish(publish_timeout)
        except Exception as exc:
            logger.debug(f"Failed to publish device-delete payload for {device.name!r} ({topic}): {exc}")

    def _republish_device_discovery(self, device: HomeAssistantDevice, publish_timeout: float | None) -> None:
        """Republish discovery for a single device. Used after entity removal so HA drops the component."""
        target_topic = f"{self._discovery_prefix}/device/{device.unique_id}/config"
        for discovery_topic, discovery_payload in self._discovery_gen():
            if discovery_topic != target_topic:
                continue
            try:
                payload_str = json.dumps(discovery_payload, separators=(",", ":"))
                logger.info(f"Republishing device discovery: topic={discovery_topic} retained=True qos={QoS.AtLeastOnce.name} bytes={len(payload_str)}")
                info = self._connection.publish(discovery_topic, payload_str, QoS.AtLeastOnce, True)
                if publish_timeout is not None:
                    info.wait_for_publish(publish_timeout)
            except Exception as exc:
                logger.debug(f"Failed to republish device discovery for {device.name!r} ({target_topic}): {exc}")
            return

    def remove_entity(self, entity: HomeAssistantEntityBase, publish_timeout: float | None = None) -> None:
        """Remove an entity from its device. Idempotent and thread-safe — safe to call while run() is active."""
        with self._runtime_lock:
            owner_device: HomeAssistantDevice | None = None
            for origin in self._origins:
                for device in origin._devices:
                    if entity in device._entities:
                        owner_device = device
                        break
                if owner_device is not None:
                    break

            if owner_device is None:
                return

            self._cleanup_entity_runtime(entity)
            try:
                owner_device._entities.remove(entity)
            except ValueError:
                pass

        self._republish_device_discovery(owner_device, publish_timeout)

    def remove_device(self, device: HomeAssistantDevice, publish_timeout: float | None = None) -> None:
        """Remove a device from its origin and from Home Assistant. Idempotent and thread-safe."""
        with self._runtime_lock:
            owner_origin: HomeAssistantOrigin | None = None
            for origin in self._origins:
                if device in origin._devices:
                    owner_origin = origin
                    break

            if owner_origin is None:
                return

            for entity in list(device.entities):
                self._cleanup_entity_runtime(entity)

            try:
                owner_origin._devices.remove(device)
            except ValueError:
                pass

        self._publish_device_delete(device, publish_timeout)

    def remove_origin(self, origin: HomeAssistantOrigin, publish_timeout: float | None = None) -> None:
        """Remove an origin and clear all its devices from Home Assistant. Idempotent and thread-safe."""
        with self._runtime_lock:
            if origin not in self._origins:
                return

            devices = list(origin._devices)
            for device in devices:
                for entity in list(device.entities):
                    self._cleanup_entity_runtime(entity)

            try:
                self._origins.remove(origin)
            except ValueError:
                pass

        for device in devices:
            self._publish_device_delete(device, publish_timeout)

    def stop(self, timeout: float | None = None) -> None:
        runtime = self.runtime()
        if runtime is None:
            return
        runtime.stop(timeout)

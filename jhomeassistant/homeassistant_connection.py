from __future__ import annotations

import json
import threading
from typing import List, Union
from jmqtt import QualityOfService as QoS, MQTTMessage, MQTTConnectionV3, MQTTConnectionV5

from jhomeassistant.features import Availability, Origin, TopicConfig
from jhomeassistant.helper import validate_discovery_prefix
from jhomeassistant.helper.abbreviations import resolve_abbreviation
from jhomeassistant.helper.scheduler import Scheduler
from jhomeassistant.homeassistant_device import HomeAssistantDevice
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
        self._devices: List[HomeAssistantDevice] = []
        self._discovery_prefix = 'homeassistant'

        self.origin = Origin()
        self.availability = Availability(self._connection.availability_topic)
        self.ha_status = TopicConfig("homeassistant/status")
        self.qos: QoS | None = None
        self.encoding: str | None = None

        self._runtime_lock = threading.RLock()
        self._runtime: _RuntimeRecord | None = None

    def discovery_prefix(self, discovery_prefix: str) -> HomeAssistantConnection:
        self._discovery_prefix = validate_discovery_prefix(discovery_prefix)
        return self

    def add_devices(self, *devices: HomeAssistantDevice) -> HomeAssistantConnection:
        for device in devices:
            self._devices.append(device)
        return self

    def _discovery_gen(self):
        for device in self._devices:
            # Origin fallback
            if self.origin.name is None:
                logger.info(f"Using device name {device.name} as origin.name because no custom name was provided.")
                self.origin.name = device.name

            # Inherit connection-level QoS/encoding if set
            if device.qos is None and self.qos is not None:
                device.qos = self.qos
                logger.info(f"Inherit connection QoS={self.qos.name} to device {device.name}")
            if device.encoding is None and self.encoding is not None:
                device.encoding = self.encoding
                logger.info(f"Inherit connection encoding={self.encoding} to device {device.name}")

            device.availability.internal_merge(self.availability)
            discovery_topic, discovery_payload = device.internal_discovery(self._discovery_prefix)

            discovery_payload = {
                **discovery_payload,
                **self.origin.internal_to_dict()
            }

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

        # wait for all publish to finish
        for i in discovery_infos:
            i.wait_for_publish(publish_timeout)

    def _entities(self):
        for device in self._devices:
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

    def _runtime_execute(self, runtime: _RuntimeRecord, schedule_resolution: float, publish_timeout: float | None, re_raise_errors: bool) -> None:
        with self._runtime_lock:
            runtime.owner_thread_id = threading.get_ident()

        try:
            if not self._connection.is_connected:
                self._connection.connect()

            self._discovery(publish_timeout)
            self._connection.subscribe(self.ha_status.topic, self.homeassistant_status)

            tasks = [schedule for entity in self._entities() for schedule in entity.schedules]
            Scheduler(*tasks).run_forever(
                schedule_resolution,
                self._connection,
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

    def stop(self, timeout: float | None = None) -> None:
        runtime = self.runtime()
        if runtime is None:
            return
        runtime.stop(timeout)

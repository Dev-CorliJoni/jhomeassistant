from __future__ import annotations

from typing import TYPE_CHECKING

from jhomeassistant.homeassistant_runtime_record import _RuntimeRecord

if TYPE_CHECKING:
    from jhomeassistant.homeassistant_connection import HomeAssistantConnection


class HomeAssistantRuntime:
    def __init__(self, owner: HomeAssistantConnection, record: _RuntimeRecord):
        self._owner = owner
        self._record = record

    def stop(self, timeout: float | None = None) -> None:
        self._owner._runtime_stop(self._record, timeout)

    def join(self, timeout: float | None = None) -> bool:
        return self._owner._runtime_join(self._record, timeout)

    @property
    def is_running(self) -> bool:
        return self._owner._runtime_is_running(self._record)

    @property
    def last_error(self) -> Exception | None:
        return self._owner._runtime_last_error(self._record)

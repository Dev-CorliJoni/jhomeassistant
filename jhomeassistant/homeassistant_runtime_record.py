from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from jhomeassistant.homeassistant_runtime import HomeAssistantRuntime


@dataclass
class _RuntimeRecord:
    state: str
    stop_event: threading.Event = field(default_factory=threading.Event)
    done_event: threading.Event = field(default_factory=threading.Event)
    thread: threading.Thread | None = None
    owner_thread_id: int | None = None
    last_error: Exception | None = None
    handle: HomeAssistantRuntime | None = None

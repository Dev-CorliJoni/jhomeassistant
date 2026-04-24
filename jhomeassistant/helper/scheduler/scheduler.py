from __future__ import annotations

import time
import threading
from typing import Callable

from jhomeassistant.helper.scheduler import Schedule


class Scheduler:
    def __init__(self, *tasks: Schedule):
        self.tasks = list(tasks)
        self._tasks_lock = threading.Lock()

    def remove_tasks(self, *tasks: Schedule) -> None:
        if not tasks:
            return
        targets = {id(t) for t in tasks}
        with self._tasks_lock:
            self.tasks = [t for t in self.tasks if id(t) not in targets]

    def run_forever(self, tick_resolution: float, get_connection: Callable, stop_event: threading.Event | None = None):
        sleep_interval = max(0.001, tick_resolution)
        while True:
            if stop_event is not None and stop_event.is_set():
                break

            now = time.time()
            with self._tasks_lock:
                snapshot = list(self.tasks)
            for t in snapshot:
                t.run(now, get_connection())

            if stop_event is None:
                time.sleep(sleep_interval)
            else:
                stop_event.wait(sleep_interval)

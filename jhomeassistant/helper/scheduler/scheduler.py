from __future__ import annotations

import time
import threading

from jhomeassistant.helper.scheduler import Schedule


class Scheduler:
    def __init__(self, *tasks: Schedule):
        self.tasks = list(tasks)

    def run_forever(self, tick_resolution: float, connection, stop_event: threading.Event | None = None):
        sleep_interval = max(0.001, tick_resolution)
        while True:
            if stop_event is not None and stop_event.is_set():
                break

            now = time.time()
            for t in self.tasks:
                t.run(now, connection)

            if stop_event is None:
                time.sleep(sleep_interval)
            else:
                stop_event.wait(sleep_interval)

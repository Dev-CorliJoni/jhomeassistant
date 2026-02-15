import time

from jhomeassistant.helper.scheduler import Schedule


class Scheduler:
    def __init__(self, *tasks: Schedule):
        self.tasks = list(tasks)

    def run_forever(self, tick_resolution: float, connection):
        while True:
            now = time.time()
            for t in self.tasks:
                t.run(now, connection)
            time.sleep(tick_resolution)

class Schedule:
    def __init__(self, interval_sec: float, func):
        self._func = func
        self._next_timestamp = 0.0
        self._interval = max(0.0, interval_sec)

    def run(self, now: float, connection):
        if now >= self._next_timestamp:
            self._func(connection)
            self._next_timestamp = now + self._interval

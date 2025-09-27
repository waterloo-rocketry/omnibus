import time


class TickCounter:
    """
    TickCounter is a wrapper class for counting ticks (events) in regular intervals,
    such as frames per second.
    """

    # count the number of ticks in the last running_average_duration seconds
    def __init__(self, running_average_duration):
        self.running_average_duration = running_average_duration
        self.count = 0
        self.timestamp_list = []

    # remove entries older than self.running_average_duration from self.timestamp_list
    def _prune(self):
        min_age = time.monotonic() - self.running_average_duration
        while len(self.timestamp_list) > 0 and self.timestamp_list[0] < min_age:
            self.timestamp_list.pop(0)

    # call this every tick
    def tick(self):
        self.timestamp_list.append(time.monotonic())
        self.count += 1

        self._prune()

    # number of ticks in the last running_average_duration seconds
    def tick_rate(self):
        self._prune()
        return len(self.timestamp_list) / self.running_average_duration

    # total number of ticks
    def tick_count(self):
        return self.count

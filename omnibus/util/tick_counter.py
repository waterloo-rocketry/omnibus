from sqlite3 import Timestamp
import time


class TickCounter:
    """
    Tick Counter is a wrapper class for counting ticks(events) in regular intervals, such as frames per second counter.

    """

    def __init__(self, running_average_length):
        self.avglen = running_average_length
        self.count = 0
        self.timestamp_list = []
        self.rate = 0

    # Call this every tick
    def tick(self):

        # Running average
        self.timestamp_list.append(time.time())
        self.count += 1

        if len(self.timestamp_list) > self.avglen:
            self.timestamp_list.pop(0)

        if len(self.timestamp_list) > 1:
            self.rate = (len(self.timestamp_list)-1) / \
                (self.timestamp_list[-1] - self.timestamp_list[0])

    def tick_rate(self):
        return self.rate

    def tick_count(self):
        return self.count

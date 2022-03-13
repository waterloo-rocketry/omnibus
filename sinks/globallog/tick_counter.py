import time


class TickCounter:

    def __init__(self):
        self.count = 0
        self.last_timestamp = time.time()
        self.last_tps = 0

    # Todo: Alternative list implementation holding recent timestamps and take average tps

    # Call this every tick
    def tick(self):
        self.count += 1
        self.last_tps = 1/(time.time()-self.last_timestamp)
        self.last_timestamp = time.time()

    def tps(self):
        return self.last_tps

    def tick_count(self):
        return self.count

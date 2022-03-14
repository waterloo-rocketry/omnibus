import time


class TickCounter:

    # avgtick is an integer noting the running average, set to 0 instanatenous rate is desired
    def __init__(self, avgtick):
        self.avgtick = avgtick
        self.count = 0
        self.last_timestamp = time.time()
        self.last_tps = 0
        self.timestamp_list = [time.time()]

    # Call this every tick
    def tick(self):

        # Running average
        if self.avgtick > 0:
            self.timestamp_list.append(time.time())
            if self.count >= self.avgtick:
                self.timestamp_list.pop(0)
            self.last_tps = len(self.timestamp_list)/(time.time() - self.timestamp_list[0])

        # Instantaneous
        else:
            self.last_tps = 1/(time.time()-self.last_timestamp)

        self.last_timestamp = time.time()
        self.count += 1

    def tps(self):
        return self.last_tps

    def tick_count(self):
        return self.count

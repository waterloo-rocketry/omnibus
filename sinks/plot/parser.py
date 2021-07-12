import time

start = time.time()

class Parser:
    def __init__(self, channel):
        self.channel = channel

    def parse(self, payload):
        raise NotImplementedError

class DAQParser(Parser):
    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        return payload["timestamp"] - start, payload["data"][self.sensor][0]

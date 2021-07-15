import re
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

timeMatcher = re.compile("t= *(\d+)ms")
valMatcher = re.compile("LEVEL=(\d+)")
class FillSensingParser(Parser):
    def __init__(self, channel):
        super().__init__(channel)

    def parse(self, payload):
        if not payload.startswith("[ FILL_LVL "):
            return

        return int(timeMatcher.search(payload).group(1)) / 1000, int(valMatcher.search(payload).group(1))

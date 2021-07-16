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

class FillSensingParser(Parser):
    timeMatcher = re.compile("t= *(\d+)ms")
    levelMatcher = re.compile("LEVEL=(\d+)")
    def __init__(self, channel):
        super().__init__(channel)

    def parse(self, payload):
        if not payload.startswith("[ FILL_LVL "):
            return

        t = int(FillSensingParser.timeMatcher.search(payload).group(1)) / 1000
        level = int(FillSensingParser.levelMatcher.search(payload).group(1))

        return t, level

class TemperatureParser(Parser):
    timeMatcher = re.compile("t= *(\d+)ms")
    sensorMatcher = re.compile("SENSOR=(\d+)")
    tempMatcher = re.compile("TEMP=([\d.]+)")
    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if not payload.startswith("[ FILL_LVL "):
            return

        sensor = int(FillSensingParser.sensorMatcher.search(payload).group(1))
        if sensor != self.sensor:
            return

        t = int(FillSensingParser.timeMatcher.search(payload).group(1)) / 1000
        temp = int(FillSensingParser.tempMatcher.search(payload).group(1))

        return t, temp

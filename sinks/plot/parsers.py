import re
import time

start = time.time()

class Parser:
    """
    Turns omnibus messages into up to one datapoint
    """
    def __init__(self, channel):
        self.channel = channel # omnibus channel to parse messages from

    def parse(self, payload):
        """
        Parse a (time, value) pair from an omnibus message payload, or return None.
        """
        raise NotImplementedError

class DAQParser(Parser):
    """
    Parses DAQ messages, returning the first datapoint for a specific sensor
    """
    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if self.sensor not in payload["data"]:
            return None

        return payload["timestamp"] - start, payload["data"][self.sensor][0]

class FillSensingParser(Parser):
    """
    Parses fill sensing messages from parsley.
    """
    timeMatcher = re.compile(r"t= *(\d+)ms")
    levelMatcher = re.compile(r"LEVEL=(\d+)")

    def parse(self, payload):
        if not payload.startswith("[ FILL_LVL "):
            return None

        # time is in milliseconds
        t = int(FillSensingParser.timeMatcher.search(payload).group(1)) / 1000
        level = int(FillSensingParser.levelMatcher.search(payload).group(1))

        return t, level

class TemperatureParser(Parser):
    """
    Parses temperature messages from parsley for a specific temperature sensor.
    """
    timeMatcher = re.compile(r"t= *(\d+)ms")
    sensorMatcher = re.compile(r"SENSOR=(\d+)")
    tempMatcher = re.compile(r"TEMP=(-?[\d.]+)")

    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if not payload.startswith("[ SENSOR_TEMP "):
            return None

        sensor = int(TemperatureParser.sensorMatcher.search(payload).group(1))
        if sensor != self.sensor:
            return None

        # time is in milliseconds
        t = int(TemperatureParser.timeMatcher.search(payload).group(1)) / 1000
        temp = float(TemperatureParser.tempMatcher.search(payload).group(1))

        return t, temp

import re

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

    start = None # The unix timestamp of the first message received (so the x axis is reasonable)

    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if self.sensor not in payload["data"]:
            return None

        if DAQParser.start is None:
            DAQParser.start = payload["timestamp"]

        return payload["timestamp"] - DAQParser.start, payload["data"][self.sensor][0]

class FillSensingParser(Parser):
    """
    Parses fill sensing messages from parsley of the form:
[ FILL_LVL                  FILL       ] t=      123ms  LEVEL=4             DIRECTION=FILLING
    """
    timeMatcher = re.compile(r"t= *(\d+)ms") # match `t=    1234ms`
    levelMatcher = re.compile(r"LEVEL=(\d+)") # match `LEVEL=12`

    def parse(self, payload):
        if not payload.startswith("[ FILL_LVL "):
            return None

        # time is in milliseconds
        t = int(FillSensingParser.timeMatcher.search(payload).group(1)) / 1000
        level = int(FillSensingParser.levelMatcher.search(payload).group(1))

        return t, level

class TemperatureParser(Parser):
    """
    Parses temperature messages from parsley for a specific temperature sensor of the form:
[ SENSOR_TEMP               TEMP_SENSE ] t=      123ms  SENSOR=4            TEMP=56.789
    """
    timeMatcher = re.compile(r"t= *(\d+)ms") # match `t=    1234ms`
    sensorMatcher = re.compile(r"SENSOR=(\d+)") # match `SENSOR=12`
    tempMatcher = re.compile(r"TEMP=(-?[\d.]+)") # match `TEMP=-12.34`

    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if not payload.startswith("[ SENSOR_TEMP "):
            return None

        sensor = int(TemperatureParser.sensorMatcher.search(payload).group(1))
        if sensor != self.sensor:
            return None

        # time is in milliseconds but we want seconds
        t = int(TemperatureParser.timeMatcher.search(payload).group(1)) / 1000
        temp = float(TemperatureParser.tempMatcher.search(payload).group(1))

        return t, temp

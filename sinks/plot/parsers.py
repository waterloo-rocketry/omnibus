class Parser:
    """
    Turns omnibus messages into up to one datapoint
    """

    def __init__(self, channel):
        self.channel = channel  # omnibus channel to parse messages from

    def parse(self, payload):
        """
        Parse a (time, value) pair from an omnibus message payload, or return None.
        """
        raise NotImplementedError


class DAQParser(Parser):
    """
    Parses DAQ messages, returning the first datapoint for a specific sensor
    """

    start = None  # The unix timestamp of the first message received (so the x axis is reasonable)

    def __init__(self, channel, sensor):
        super().__init__(channel)
        self.sensor = sensor

    def parse(self, payload):
        if self.sensor not in payload["data"]:
            return None

        if DAQParser.start is None:
            DAQParser.start = payload["timestamp"]

        return payload["timestamp"] - DAQParser.start, payload["data"][self.sensor][0]


class ParsleyParser(Parser):
    def __init__(self, channel, msg_type, key):
        super().__init__(channel)
        self.msg_type = msg_type
        self.key = key
        # the timestamp of CAN messages wraps around decently frequently, account for it by storing
        self.last_time = 0  # the last recievied the time (to detect wrap arounds)
        self.time_offset = 0  # and what to add to each timestamp we recieve

    def parse(self, payload):
        if payload["msg_type"] != self.msg_type:
            return None

        if not self.filter(payload):
            return None

        if "time" in payload["data"]:
            if payload["data"]["time"] < self.last_time:  # if we've wrapped around
                self.time_offset += self.last_time  # increase the amount we need to add
            self.last_time = payload["data"]["time"]
            payload["data"]["time"] += self.time_offset

        return self.parse_can(payload)

    def filter(self, payload):
        return True

    def parse_can(self, payload):
        # time is in milliseconds but we want seconds
        t = payload["data"]["time"] / 1000
        v = payload["data"][self.key]

        return t, v


class FillSensingParser(ParsleyParser):
    def __init__(self, channel):
        super().__init__(channel, "FILL_LVL", "level")


class TemperatureParser(ParsleyParser):
    def __init__(self, channel, sensor):
        super().__init__(channel, "SENSOR_TEMP", "temperature")
        self.sensor = sensor

    def filter(self, payload):
        return payload["data"]["sensor_id"] == self.sensor


class AccelParser(ParsleyParser):
    def __init__(self, channel, axis):
        super().__init__(channel, "SENSOR_ACC", axis)


class AnalogSensorParser(ParsleyParser):
    def __init__(self, channel, sensor):
        super().__init__(channel, "SENSOR_ANALOG", "value")
        self.sensor = sensor

    def filter(self, payload):
        return payload["data"]["sensor_id"] == self.sensor

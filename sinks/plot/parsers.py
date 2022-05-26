from collections import defaultdict

from series import Series


class SeriesDefaultDict(defaultdict):
    """
    Let us call `self.series["xyz"].add(...)` whether or not "xyz" is an existing series.
    """

    def __missing__(self, key):
        self[key] = Series(key)
        return self[key]


class Parser:
    """
    Turns omnibus messages into series of their data
    """

    parsers = []  # keep track of all initialized parsers

    def __init__(self, channel):
        self.channel = channel  # omnibus channel to parse messages from
        self.series = SeriesDefaultDict()  # series this parser is populating

        Parser.parsers.append(self)

    def parse(self, payload):
        """
        Add all datapoints from an omnibus message payload to the corresponding self.series
        """
        raise NotImplementedError

    @staticmethod
    def all_parse(channel, payload):
        for parser in Parser.parsers:
            if channel.startswith(parser.channel):
                parser.parse(payload)

    @staticmethod
    def get_series():
        res = []
        for parser in Parser.parsers:
            res += parser.series.values()
        return res

    def get_serie(name):
        for parser in Parser.parsers:
            if parser.series.values().name == name:
                return parser.series.values()
        return None

class DAQParser(Parser):
    """
    Parses DAQ messages, returning the average for each sensor in each message
    """

    def __init__(self):
        super().__init__("DAQ")
        # The unix timestamp of the first message received (so the x axis is reasonable)
        self.start = None

    def parse(self, payload):
        if self.start is None:
            self.start = payload["timestamp"]

        time = payload["timestamp"] - self.start

        for sensor, data in payload["data"].items():
            self.series[sensor].add(time, sum(data)/len(data))


DAQParser()


class ParsleyParser(Parser):
    """
    Handles rolling over of parsley timestamps.
    """

    def __init__(self, msg_type):
        super().__init__("CAN/Parsley")
        self.msg_type = msg_type
        # the timestamp of CAN messages wraps around decently frequently, account for it by storing
        self.last_time = 0  # the last recievied time (to detect wrap arounds)
        self.time_offset = 0  # and what to add to each timestamp we recieve

    def parse(self, payload):
        if payload["msg_type"] != self.msg_type:
            return

        if "time" in payload["data"]:
            # time is in milliseconds but we want seconds
            payload["data"]["time"] /= 1000

            if payload["data"]["time"] < self.last_time:  # if we've wrapped around
                self.time_offset += self.last_time  # increase the amount we need to add
            self.last_time = payload["data"]["time"]
            payload["data"]["time"] += self.time_offset

        self.parse_can(payload)

    def parse_can(self, payload):
        raise NotImplementedError


class FillSensingParser(ParsleyParser):
    def __init__(self):
        super().__init__("FILL_LVL")

    def parse_can(self, payload):
        t = payload["data"]["time"]
        v = payload["data"]["level"]

        self.series["Fill Level"].add(t, v)


FillSensingParser()


class TemperatureParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_TEMP")

    def parse_can(self, payload):
        s = payload["data"]["sensor_id"]
        t = payload["data"]["time"]
        v = payload["data"]["temperature"]

        self.series[f"Temperature {s}"].add(t, v)


TemperatureParser()


class AccelParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_ACC")

    def parse_can(self, payload):
        t = payload["data"]["time"]

        for axis in "xyz":
            self.series[f"Acceleration ({axis})"].add(t, payload["data"][axis])


AccelParser()


class AnalogSensorParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_ANALOG")

    def parse_can(self, payload):
        s = payload["data"]["sensor_id"]
        t = payload["data"]["time"]
        v = payload["data"]["value"]

        self.series[f"CAN Sensor {s}"].add(t, v)


AnalogSensorParser()

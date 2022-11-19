from collections import defaultdict

from series import Publisher

BOARD_NAME_LIST = ["DUMMY", "INJECTOR", "LOGGER", "RADIO", "SENSOR", "VENT", "GPS", "ARMING",
                   "PAPA", "ROCKET_PI", "ROCKET_PI_2", "SENSOR_2", "SENSOR_3"]

publisher = Publisher()

class Parser:
    """
    Turns omnibus messages into series of their data
    """

    parsers = {}  # keep track of all initialized parsers

    def __init__(self, channel, *series_kargs, **series_kwargs):
        self.channel = channel  # omnibus channel to parse messages from
        if channel not in Parser.parsers:
            publisher.add_serie(*series_kargs)
        parsers = Parser.parsers.get(channel, [])
        parsers.append(self)
        Parser.parsers[channel] = parsers

    def parse(self, payload):
        """
        Add all datapoints from an omnibus message payload to the corresponding self.series
        """
        raise NotImplementedError

    @staticmethod
    def all_parse(channel, payload):
        for ch, parsers in Parser.parsers.items():
            if channel.startswith(ch):
                for parser in parsers:
                    parser.parse(payload)

    @staticmethod
    def get_all_series(channel=""):
        res = []
        for chan, parsers in Parser.parsers.items():
            if chan.startswith(channel):
                res += parsers[0].series.values()
        return res

    @staticmethod
    def get_series(channel, name):
        """
        Return the series specified by channel and name, creating it if it doesn't exist
        """
        if channel not in Parser.parsers:
            return None
        return Parser.parsers[channel][0].series[name]  # SeriesDefaultDict takes care of the rest


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
            publisher.update(sensor, [time, sum(data)/len(data)])


DAQParser()


class ParsleyParser(Parser):
    """
    Handles rolling over of parsley timestamps.
    """

    def __init__(self, msg_type):
        super().__init__("CAN/Parsley")
        self.msg_type = msg_type
        # the timestamp of CAN messages wraps around decently frequently, account for it by storing

    def parse(self, payload):
        if payload["msg_type"] != self.msg_type:
            return

        if "time" in payload["data"]:
            # time is in milliseconds but we want seconds
            payload["data"]["time"] /= 1000

        self.parse_can(payload)

    def parse_can(self, payload):
        raise NotImplementedError


class FillSensingParser(ParsleyParser):
    def __init__(self):
        super().__init__("FILL_LVL")

    def parse_can(self, payload):
        t = payload["data"]["time"]
        v = payload["data"]["level"]

        ["Fill Level"].update([t, v])


FillSensingParser()


class TemperatureParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_TEMP")

    def parse_can(self, payload):
        s = payload["data"]["sensor_id"]
        t = payload["data"]["time"]
        v = payload["data"]["temperature"]

        publisher.update(format("Temperature {s}"), [t, v, "(C)"])


TemperatureParser()


class AccelParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_ACC")

    def parse_can(self, payload):
        t = payload["data"]["time"]

        for axis in "xyz":
            publisher.update(format("Acceleration ({axis})"),[t, payload["data"][axis]])


AccelParser()


class GyroParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_GYRO")

    def parse_can(self, payload):
        t = payload["data"]["time"]

        for axis in "xyz":
           publisher.update(format("Gyro ({axis})"),[t, payload["data"][axis]])


GyroParser()


class MagParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_MAG")

    def parse_can(self, payload):
        t = payload["data"]["time"]

        for axis in "xyz":
            publisher.update(format("Magnetometer ({axis})"),[t, payload["data"][axis]])


MagParser()


class AnalogSensorParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_ANALOG")

    def parse_can(self, payload):
        s = payload["data"]["sensor_id"]
        t = payload["data"]["time"]
        v = payload["data"]["value"]
        b = payload["board_id"]

        if s.startswith("SENSOR_PRESSURE") or s == "SENSOR_VENT_TEMP":
            if v >= 2**15:
                v -= 2**16

        publisher.update(format("CAN Sensor {b} {s}"),[t, v])


AnalogSensorParser()


class ActuatorStateParser(ParsleyParser):
    def __init__(self):
        super().__init__("ACTUATOR_STATUS")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        act = payload["data"]["actuator"]
        req = payload["data"]["req_state"]
        cur = payload["data"]["cur_state"]

        v = 0
        if req == "ACTUATOR_OPEN":
            v += 0
        elif req == "ACTUATOR_CLOSED":
            v += 30
        else:
            v += 60

        if cur == "ACTUATOR_OPEN":
            v += 0
        if cur == "ACTUATOR_CLOSED":
            v += 3
        else:
            v += 6

        publisher.update(format("actuator state ({act})"), [time, v, "(0 open 3 closed 6 unknown, req * 10 + cur)"])


ActuatorStateParser()


class GPSInfoParser(ParsleyParser):
    def __init__(self):
        super().__init__("GPS_INFO")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        numsat = payload["data"]["num_sats"]
        qual = payload["data"]["quality"]
        publisher.update("GPS Satellites",[time, numsat])
        publisher.update("GPS Quality",[time, qual])


GPSInfoParser()


class GPSAltParser(ParsleyParser):
    def __init__(self):
        super().__init__("GPS_ALTITUDE")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        alt = payload["data"]["altitude"]
        dalt = payload["data"]["daltitude"]
        publisher.update("GPS Altitude", [time, alt + dalt / 100])


GPSAltParser()


class GPSLatitudeParser(ParsleyParser):
    def __init__(self):
        super().__init__("GPS_LATITUDE")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        degs = payload["data"]["degs"]
        mins = payload["data"]["mins"]
        dmins = payload["data"]["dmins"]
        publisher.update("GPS Latitude",[time, degs + mins / 60 + dmins / 600000])


GPSLatitudeParser()


class GPSLongitudeParser(ParsleyParser):
    def __init__(self):
        super().__init__("GPS_LONGITUDE")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        degs = payload["data"]["degs"]
        mins = payload["data"]["mins"]
        dmins = payload["data"]["dmins"]
        publisher.update("GPS Longitude", [time, degs + mins / 60 + dmins / 600000])


GPSLongitudeParser()


class SensorAltParser(ParsleyParser):
    def __init__(self):
        super().__init__("SENSOR_ALTITUDE")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        alt = payload["data"]["altitude"]
        publisher.update("Sensor Altitude",[time, alt])


class ArmStatusParser(ParsleyParser):
    def __init__(self):
        super().__init__("ALT_ARM_STATUS")

    def parse_can(self, payload):
        time = payload["data"]["time"]
        state = payload["data"]["state"]
        num = payload["data"]["altimeter"]
        drogue = payload["data"]["drogue_v"]
        main = payload["data"]["main_v"]

        if state == "ARMED":
            arm_value = 1
        elif state == "DISARMED":
            arm_value = 0
        else:
            arm_value = 2

        publisher.update(format("Arm State {num}"),[time, arm_value, "(0 DISARMED 1 ARMED 2 UNKNOWN)"])
        publisher.update(format("Arm Drogue Voltage ({num})"),[time, drogue, "(mV)"])
        publisher.update(format("Arm Main Voltage ({num})"),[time, main, "(mV)"])


ArmStatusParser()


class CanDisplayParser(Parser):
    def __init__(self):
        super().__init__("CAN/Parsley")

    @staticmethod
    def parse(payload):
        if payload["board_id"] in BOARD_NAME_LIST:
            CanDisplayParser.canSeries[payload["board_id"]].publisher.update([payload])

    @staticmethod
    def get_canSeries(board_id):
        if board_id in BOARD_NAME_LIST:
            return CanDisplayParser.canSeries[board_id]
        return None

    @staticmethod
    def get_all_series():
        return CanDisplayParser.canSeries.values()


CanDisplayParser()

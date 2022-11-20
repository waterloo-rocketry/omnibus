from series import Publisher

_func_map = {}
publisher = Publisher()
# decorator for parse functions to save a massive if chain
def register(msg_channels):
    if isinstance(msg_channels, str):
        msg_channels = [msg_channels]

    def wrapper(fn):
        for msg_channel in msg_channels:
            for func in _func_map:
                if func.startswith(msg_channel):
                    raise KeyError(f"Duplicate parsers for message type {msg_channel}")
            _func_map[msg_channel] = fn
        return fn
    return wrapper


@register("DAQ")
def daq_parser(msg_data):
    timestamp = msg_data["timestamp"]

    for sensor, data in msg_data["data"].items():
        publisher.update(sensor, [timestamp, data])

def parse(msg_channel, msg_payload):
    for func in _func_map:
        if msg_channel.startswith(func):
            _func_map[func](msg_payload)


######################################## OLD CODE #############################################
#
BOARD_NAME_LIST = ["DUMMY", "INJECTOR", "LOGGER", "RADIO", "SENSOR", "VENT", "GPS", "ARMING",
                   "PAPA", "ROCKET_PI", "ROCKET_PI_2", "SENSOR_2", "SENSOR_3"]
@register(BOARD_NAME_LIST)
def can_parser(msg_data):
    timestamp = msg_data["timestamp"]

    for sensor, data in msg_data["data"].items():
        publisher.update(sensor, [timestamp, data])
#
#from series import CanMsgSeries
#
#class Parser:
#    """
#    Turns omnibus messages into series of their data
#    """
#
#    parsers = {}  # keep track of all initialized parsers
#
#    def __init__(self, channel, *series_kargs, **series_kwargs):
#        self.channel = channel  # omnibus channel to parse messages from
#
#        if channel in Parser.parsers:
#            self.series = Parser.parsers[channel][0].series
#        else:
#            self.series = SeriesDefaultDict(*series_kargs, **series_kwargs)
#        parsers = Parser.parsers.get(channel, [])
#        parsers.append(self)
#        Parser.parsers[channel] = parsers
#
#    def parse(self, payload):
#        """
#        Add all datapoints from an omnibus message payload to the corresponding self.series
#        """
#        raise NotImplementedError
#
#    @staticmethod
#    def all_parse(channel, payload):
#        for ch, parsers in Parser.parsers.items():
#            if channel.startswith(ch):
#                for parser in parsers:
#                    parser.parse(payload)
#
#    @staticmethod
#    def get_all_series(channel=""):
#        res = []
#        for chan, parsers in Parser.parsers.items():
#            if chan.startswith(channel):
#                res += parsers[0].series.values()
#        return res
#
#    @staticmethod
#    def get_series(channel, name):
#        """
#        Return the series specified by channel and name, creating it if it doesn't exist
#        """
#        if channel not in Parser.parsers:
#            return None
#        return Parser.parsers[channel][0].series[name]  # SeriesDefaultDict takes care of the rest
#
#class CanDisplayParser(Parser):

#
#    def __init__(self):
#        super().__init__("CAN/Parsley")
#
#    @staticmethod
#    def parse(payload):
#        if payload["board_id"] in BOARD_NAME_LIST:
#            CanDisplayParser.canSeries[payload["board_id"]].add(payload)
#
#    @staticmethod
#    def get_canSeries(board_id):
#        if board_id in BOARD_NAME_LIST:
#            return CanDisplayParser.canSeries[board_id]
#        return None
#
#    @staticmethod
#    def get_all_series():
#        return CanDisplayParser.canSeries.values()
#
#
#CanDisplayParser()

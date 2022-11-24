from publisher import publisher

_func_map = {}
# decorator for parse functions to save a massive if chain


def register(msg_channels):
    if isinstance(msg_channels, str):
        msg_channels = [msg_channels]

    def wrapper(fn):
        for msg_channel in msg_channels:
            if msg_channel in _func_map:
                raise KeyError(f"Duplicate parsers for message type {msg_channel}")
            _func_map[msg_channel] = fn
        return fn
    return wrapper


@register("DAQ")
def daq_parser(msg_data):
    timestamp = msg_data["timestamp"]
    parsed_messages = []

    for sensor, data in msg_data["data"].items():
        parsed_messages.append((sensor + "|DAQ" , timestamp, sum(data)/len(data)))

    return parsed_messages

################### CAN Stuff, WIP ######################
"""
CAN/Parsley parser needs revamp and will not be included in the scope of the series_revamp PR for the time being.
Therefore, it will be left commented out and not functional as of series_revamp PR as of Nov 2022.
"""

# BOARD_NAME_LIST = ["DUMMY", "INJECTOR", "LOGGER", "RADIO", "SENSOR", "VENT", "GPS", "ARMING",
#                    "PAPA", "ROCKET_PI", "ROCKET_PI_2", "SENSOR_2", "SENSOR_3"]
# 
# @register("CAN")
# def can_parser(payload):
#     print(payload)
#     timestamp = msg_data["timestamp"]
#     parsed_messages = []
# 
#     for board, data in msg_data["data"].items():
#         parsed_messages.append((board + "|CAN", timestamp, sum(data) / len(data)))
# 
#     return parsed_messages

def parse(msg_channel, msg_payload):
    for func in _func_map:
        if msg_channel.startswith(func):
            series_message_pair_list = _func_map[func](msg_payload)
            for series_name, timestamp, parsed_message in series_message_pair_list:
                publisher.update(series_name, [timestamp, parsed_message])

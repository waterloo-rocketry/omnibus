from typing import List, Tuple, Union, Any

from publisher import publisher

import time

# decorator for parse functions to save a massive if chain
# https://peps.python.org/pep-0318/#current-syntax

"""
tl;dr

@Register("Chan")
def func(msg):
    ...

reduces to

func = Register("Chan")(func)

which further reduces to

func = Register("Chan").__call__(func)
"""

# When a function is registered to a particular channel
# using the Register decorator, it is added to the
# function map. IE,
#   func_map[channel].append(function)
# Then, when parse is called, it searches


class Register:
    func_map: dict = {}

    def __init__(self, msg_channels: Union[str, List[str]]):
        if isinstance(msg_channels, str):
            self.msg_channels = [msg_channels]
        else:
            self.msg_channels = msg_channels

    def __call__(self, func):
        for msg_channel in self.msg_channels:
            if msg_channel not in Register.func_map:
                Register.func_map[msg_channel] = [func]
            else:
                Register.func_map[msg_channel].append(func)

        return func


def parse(msg_channel: str, msg_payload: Any) -> None:
    # Note: Assuming that msg_channel is a string and msg_payload can be of any type
    for channel in Register.func_map:
        if msg_channel.startswith(channel):
            for func in Register.func_map[channel]:
                # For an explanation, please refer to the later block of comments
                for stream_name, timestamp, parsed_message in func(msg_payload):
                    publisher.update(stream_name, (timestamp, parsed_message))

# We insist that each parse have the following signature
# parser : message -> [(stream_name, timestamp, parsed_message) ...]

# After the parser is called, the stream, stream_name is updated with the message
# [timestamp, parsed_message]

# the reason we do this, rather than having the parser directly update the streams is
# to enable unit testing of this following code

# We note that parsers may use the func_map to call other parsers (This is how we plan
# to handle CAN messages in the future)


@Register("DAQ")
def daq_parser(msg_data: dict) -> List[Tuple[str, int, float]]:
    timestamp = msg_data["timestamp"]
    parsed_messages = []

    for sensor, data in msg_data["data"].items():
        parsed_messages.append((sensor, timestamp, sum(data)/len(data)))

    return parsed_messages


# map between message types and fields that we need to split data based on
splits: dict = {
    "ACTUATOR_CMD": "actuator",
    "ALT_ARM_CMD": "altimeter",
    "ACTUATOR_STATUS": "actuator",
    "ALT_ARM_STATUS": "altimeter",
    "SENSOR_TEMP": "sensor_id",
    "SENSOR_ANALOG": "sensor_id",
}
last_timestamp: dict = {}  # Last timestamp seen for each board + message type
offset_timestamp: dict = {}  # per-board-and-message offset to account for time rollovers


@Register("CAN/Parsley")
def can_parser(payload: dict) -> List[Tuple[str, Union[float, int], Union[str, int]]]:
    # Note: Assuming that the payload of a CAN message is a dictionary
    # Payload is a dictionary representing the parsed CAN message. We need to break
    # it into individual streams of data so we can plot / display / etc.
    # The main complication is that we need to split those streams in a message-
    # specific way, eg SENSOR_ANALOG messages need a different stream for each
    # value of SENSOR_ID.

    # Example payload: {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'data': {'time': 37.595, 'sensor_id': 'SENSOR_GROUND_VOLT', 'value': 13104}}

    message_type = payload["msg_type"]
    board_id = payload["board_id"]
    data = payload["data"]

    # Build up the common prefix for all data streams, split based on a field if needed.
    prefix = f"{board_id}/{message_type}"
    if message_type in splits:
        split = data.pop(splits[message_type])
        prefix += f"/{split}"

    error_series = []  # additional series to publish to on error

    timestamp = data.pop("time", time.time())  # default back to system time
    time_key = board_id + message_type
    if time_key not in last_timestamp:
        last_timestamp[time_key] = 0
        offset_timestamp[time_key] = 0
        publisher.ensure_exists(f"{board_id}/RESET")
        publisher.ensure_exists(f"{board_id}/ERROR")
    if timestamp < last_timestamp[time_key] - 5 and timestamp < 10:  # detect rollover
        offset_timestamp[time_key] += last_timestamp[time_key]
        if message_type == "GENERAL_BOARD_STATUS":
            error_series.append((f"{board_id}/RESET", time.time(), time.strftime("%I:%M:%S")))
    last_timestamp[time_key] = timestamp
    timestamp += offset_timestamp[time_key]

    if message_type == "GENERAL_BOARD_STATUS" and data['status'] != "E_NOMINAL":
        error_series.append((f"{board_id}/ERROR", timestamp, payload["data"]))

    return [(f"{prefix}/{field}", timestamp, value) for field, value in data.items()] + error_series


@Register("RLCS")
def rlcs_parser(payload: dict) -> List[Tuple[str, float, Union[str, int]]]:
    # Note: Assuming that the payload for the RLCS parser is a dictionary
    timestamp = time.time()
    return [(f"RLCS/{k}", timestamp, v) for k, v in payload.items()]


@Register("Parsley/Health")
def parsley_health(payload: dict) -> List[Tuple[str, float, bool]]:
    # Note: Assuming that the payload for the Parsley Health parser is a dictionary
    return [(f"Parsley {payload['id']} health", time.time(), payload["healthy"])]


@Register("StateEstimation")
def state_est_parser(payload: dict) -> List[Tuple[str, float, Union[str, int]]]:
    # Note: Assuming that the payload for the State Estimation parser is a dictionary
    timestamp = payload["timestamp"]
    return [
        ("StateEstimation/Orientation", timestamp, payload["data"]["orientation"]),
        ("StateEstimation/Position", timestamp, payload["data"]["position"])
    ]


@Register("")
def all_parser(_) -> List[Tuple[str, int, int]]:
    return [("ALL", 0, -1)]

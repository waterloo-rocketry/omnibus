from publisher import publisher

import time
from collections.abc import Callable
from typing import Any, TypeVar

_ParserFn = Callable[[Any], list[tuple[str, float, Any]]]
_P = TypeVar("_P", bound=_ParserFn)

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
    func_map: dict[str, list[Callable[..., Any]]] = {}

    def __init__(self, msg_channels: str | list[str]) -> None:
        if isinstance(msg_channels, str):
            self.msg_channels: list[str] = [msg_channels]
        else:
            self.msg_channels = msg_channels

    def __call__(self, func: _P) -> _P:
        for msg_channel in self.msg_channels:
            if msg_channel not in Register.func_map:
                Register.func_map[msg_channel] = [func]
            else:
                Register.func_map[msg_channel].append(func)

        return func


def parse(msg_channel: str, msg_payload: Any) -> None:
    for channel in Register.func_map:
        if msg_channel.startswith(channel):
            for func in Register.func_map[channel]:
                # For an explanation, please refer to later block of comments
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
def daq_parser(msg_data: dict[str, Any]) -> list[tuple[str, float, Any]]:
    timestamp = msg_data["timestamp"]
    parsed_messages: list[tuple[str, float, Any]] = []

    for sensor, data in msg_data["data"].items():
        parsed_messages.append((sensor, timestamp, sum(data)/len(data)))

    return parsed_messages


last_timestamp: dict[str, float] = {}  # Last timestamp seen for each board + message type
offset_timestamp: dict[str, float] = {}  # per-board-and-message offset to account for time rollovers


@Register("CAN/Parsley")
def can_parser(payload: dict[str, Any]) -> list[tuple[str, float, Any]]:
    # Payload is a dictionary representing the parsed CAN message. We need to break
    # it into individual streams of data so we can plot / display / etc.
    # In parsley 2026.3 msg_metadata carries the per-message identity (sensor/actuator/
    # altimeter id), so we always embed it in the stream prefix to split streams.

    # Example payload: {'board_type_id': 'INJECTOR', 'board_inst_id': 'ROCKET',
    #   'msg_prio': 'LOW', 'msg_type': 'SENSOR_ANALOG32',
    #   'msg_metadata': 'SENSOR_PT_CHANNEL_1', 'data': {'time': 37.595, 'value': 1310}}

    message_type: str = payload["msg_type"]
    board_type_id: str = payload["board_type_id"]
    board_inst_id: str = payload["board_inst_id"]
    metadata: Any = payload["msg_metadata"]
    data: dict[str, Any] = payload["data"]

    prefix = f"{board_type_id}/{board_inst_id}/{message_type}/{metadata}"

    error_series: list[tuple[str, float, Any]] = []  # additional series to publish to on error

    timestamp: float = data.pop("time", time.time())  # default back to system time
    time_key = board_type_id + board_inst_id + message_type
    if time_key not in last_timestamp:
        last_timestamp[time_key] = 0
        offset_timestamp[time_key] = 0
        publisher.ensure_exists(f"{board_type_id}/{board_inst_id}/RESET")
        publisher.ensure_exists(f"{board_type_id}/{board_inst_id}/ERROR")
    if timestamp < last_timestamp[time_key] - 5 and timestamp < 10:  # detect rollover
        offset_timestamp[time_key] += last_timestamp[time_key]
        if message_type == "GENERAL_BOARD_STATUS":
            error_series.append((f"{board_type_id}/{board_inst_id}/RESET", time.time(), time.strftime("%I:%M:%S")))
    last_timestamp[time_key] = timestamp
    timestamp += offset_timestamp[time_key]

    err_topic = f"{board_type_id}/{board_inst_id}/ERROR"

    if message_type == "GENERAL_BOARD_STATUS":
        board_bits = data.get("board_error_bitfield")
        if board_bits != "E_NOMINAL":
            error_series.append((err_topic, timestamp, board_bits))
    
    return [(f"{prefix}/{field}", timestamp, value) for field, value in data.items()] + error_series


@Register("RLCS")
def rlcs_parser(payload: dict[str, Any]) -> list[tuple[str, float, Any]]:
    timestamp = time.time()
    return [(f"RLCS/{k}", timestamp, v) for k, v in payload.items()]


@Register("Parsley/Health")
def parsley_health(payload: dict[str, Any]) -> list[tuple[str, float, Any]]:
    return [(f"Parsley health {payload['id']}", time.time(), payload["healthy"])]


@Register("StateEstimation")
def state_est_parser(payload: dict[str, Any]) -> list[tuple[str, float, Any]]:
    timestamp: float = payload["timestamp"]
    return [
        ("StateEstimation/Orientation", timestamp, payload["data"]["orientation"]),
        ("StateEstimation/Position", timestamp, payload["data"]["position"])
    ]


@Register("")
def all_parser(_: Any) -> list[tuple[str, float, Any]]:
    return [("ALL", 0, -1)]

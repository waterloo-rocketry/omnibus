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

@register("CAN")
def can_parser(payload):
    return [("CAN", payload["data"]["time"], payload)]
    # Hacky fix so that the parse function behaves the same way
    # Since the "parsing" of the payload itself happens directly at the front end

def parse(msg_channel, msg_payload):
    for func in _func_map:
        if msg_channel.startswith(func):
            series_message_pair_list = _func_map[func](msg_payload)
            for series_name, timestamp, parsed_message in series_message_pair_list:
                publisher.update(series_name, [timestamp, parsed_message])

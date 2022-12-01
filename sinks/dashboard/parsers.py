from publisher import publisher

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
    func_map = {}
    def __init__(self, msg_channels):
        if isinstance(msg_channels, str):
            self.msg_channels = [msg_channels]
        else:
            self.msg_channels = msg_channels

    def __call__(self, func):
        for msg_channel in self.msg_channels:
            if msg_channel in Register.func_map:
                Register.func_map[msg_channel].append(func)
            Register.func_map[msg_channel] = [func]
        return func

def parse(msg_channel, msg_payload):
    for channel in Register.func_map:
        if msg_channel.startswith(channel):
            for func in Register.func_map[channel]:
                # For an explanation, please refer to later block of comments
                stream_message_pair_list = func(msg_payload)
                for stream_name, timestamp, parsed_message in stream_message_pair_list:
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
def daq_parser(msg_data):
    timestamp = msg_data["timestamp"]
    parsed_messages = []

    for sensor, data in msg_data["data"].items():
        parsed_messages.append(("DAQ|" + sensor , timestamp, sum(data)/len(data)))

    return parsed_messages

@Register("CAN")
def can_parser(payload):
    return [("CAN", payload["data"]["time"], payload)]
    # Note, we plan to revist the way that CAN message are handled

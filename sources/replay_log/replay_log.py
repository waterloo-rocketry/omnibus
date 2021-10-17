"""
Replay Log Source
-  
Replays previous logs from the Global Log sink,
or from a selected file, in real time.

See python3 main.py --help for options.
"""

import time
import msgpack

from omnibus import Sender, Message


def replay(log_file, replay_speed):
    """
    Replays the contents of a log_file
    """
    unpacker = None
    with open(log_file, 'rb') as f:
        unpacker = msgpack.Unpacker(file_like=f)

        r_start_time = time.time()  # real start time
        l_start_time = None         # log start time

        sender = Sender()
        while True:
            message = fetch_message(unpacker)
            if message == None:
                break

            if l_start_time == None:
                l_start_time = message.timestamp

            wait_for_logtime(message, r_start_time, l_start_time, replay_speed)

            """
            Note that we use send_message() over send() here, 
            keeping the old timestamp, message.timestamp.
            """
            sender.send_message(message)


def fetch_message(unpacker):
    """
    Fetch the next message from unpacker
    """
    try:
        channel, timestamp, payload = unpacker.unpack()
        return Message(channel, timestamp, payload)
    except msgpack.exceptions.OutOfData as e:
        return None


def wait_for_logtime(message, r_start_time, l_start_time, replay_speed):
    r_delta = (time.time() - r_start_time) * replay_speed
    l_delta = message.timestamp - l_start_time

    # wait for real time to catch-up to log time
    while r_delta < l_delta:
        r_delta = (time.time() - r_start_time) * replay_speed

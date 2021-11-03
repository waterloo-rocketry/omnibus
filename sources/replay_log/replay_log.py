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

    with open(log_file, 'rb') as f:
        unpacker = msgpack.Unpacker(file_like=f)

        r_start_time = time.time()  # real start time
        l_start_time = None         # log start time

        sender = Sender()
        for channel, timestamp, payload in unpacker:
            if l_start_time == None:
                l_start_time = timestamp

            wait_for_logtime(timestamp, r_start_time, l_start_time, replay_speed)

            """
            Note that we use send_message() over send(), 
            keeping the old timestamp.
            """
            sender.send_message(Message(channel, timestamp, payload))


def wait_for_logtime(msg_timestamp, r_start_time, l_start_time, replay_speed):
    r_delta = 0
    l_delta = msg_timestamp - l_start_time

    # wait for real time to catch-up to log time
    while r_delta < l_delta:
        r_delta = (time.time() - r_start_time) * replay_speed

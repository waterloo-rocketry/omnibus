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

def wait_for_logtime(msg_timestamp, real_start, log_start, replay_speed):
    r_delta = 0
    l_delta = msg_timestamp - log_start
    # wait for real time to catch-up to log time
    while r_delta < l_delta:
        r_delta = (time.time() - real_start) * replay_speed

def replay(log_buffer, replay_speed):
    """
    Replays the contents of a log_buffer
    """
    unpacker = msgpack.Unpacker(file_like=log_buffer)
    real_start = time.time()
    log_start = None
    sender = Sender()
    for channel, timestamp, payload in unpacker:
        if log_start == None:
            log_start = timestamp
        wait_for_logtime(timestamp, real_start, log_start, replay_speed)
        # send_message(...) instead of send(...) keeps old timestamp
        sender.send_message(Message(channel, timestamp, payload))

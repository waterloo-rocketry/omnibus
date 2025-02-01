"""
Replay Log Source
-
Replays previous logs from the Global Log sink,
or from a selected file, in real time.

See python3 main.py --help for options.
"""

import io
import time

import msgpack

from omnibus import Sender, Message


def replay(log_buffer: io.BufferedReader, replay_speed: float | int):
    """
    Replays the contents of a log_buffer
    """
    unpacker = msgpack.Unpacker(file_like=log_buffer)
    real_start = time.time()
    log_start = None
    sender = Sender()
    print("Replaying...")
    for channel, timestamp, payload in unpacker:
        if log_start == None:
            log_start = timestamp
        while timestamp - log_start > (time.time() - real_start) * replay_speed:
            time.sleep(0.1)
        # send_message(...) instead of send(...) keeps old timestamp
        sender.send_message(Message(channel, timestamp, payload))
        print(f"\r{timestamp - log_start:.0f}               ", end='')

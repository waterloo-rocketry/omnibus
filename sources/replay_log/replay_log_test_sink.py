from datetime import datetime

import msgpack

from omnibus import Receiver

# Will log all messages passing through bus
CHANNEL = ""
FNAME = "./sources/replay_log/test_log_out.log"

def log_test_logs():
    receiver = Receiver(CHANNEL)
    with open(FNAME, "ab") as f:
        while True:
            msg = receiver.recv_message(timeout=1000)
            if msg == None:
                break
            f.write(msgpack.packb([msg.channel, msg.timestamp, msg.payload]))


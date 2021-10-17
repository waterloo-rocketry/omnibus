# Global logger - Saves messages passed through bus to asc-time.log

from datetime import datetime

import msgpack

from omnibus import Receiver

# Will log all messages passing through bus
CHANNEL = ""
# Retrieves current date and time
CURTIME = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
# Creates filename
fname = CURTIME + ".log"
receiver = Receiver(CHANNEL)
# Creates new file
with open(fname, "ab") as f:
    while True:
        msg = receiver.recv_message()
        f.write(msgpack.packb([msg.channel, msg.timestamp, msg.payload]))

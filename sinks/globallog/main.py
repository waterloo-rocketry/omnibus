# Global logger - Saves messages passed through bus to asc-time.log

from datetime import datetime

from omnibus import Receiver

# Will log all messages passing through bus
CHANNEL = ""
SERVER = "tcp://localhost:5076"
# Retrieves current date and time
CURTIME = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
# Creates filename
fname = CURTIME + ".log"
receiver = Receiver(SERVER, CHANNEL)
# Creates new file
with open(fname, "w") as f:
    while True:
        msg = receiver.recv_message()
        f.write(f"{msg.timestamp} :: {msg.channel} :: {msg.payload}")

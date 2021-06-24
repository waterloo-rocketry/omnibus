# Printer - Prints payload of all messages on a channel.

import sys

from omnibus import Receiver

SERVER = "tcp://localhost:5076"

# Take a channel as a command line argument. Defaults to all channels.
channel = ""
if len(sys.argv) > 1:
    channel = sys.argv[1]
receiver = Receiver(SERVER, channel)

while True:
    data = receiver.recv()
    print(data)

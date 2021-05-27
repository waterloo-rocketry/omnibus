# Printer - Prints payload of all messages on a channel.

import sys

from omnibus import Receiver

# Take a channel as a command line argument. Defaults to all channels.
channel = ""
if len(sys.argv) > 1:
    channel = sys.argv[1]
receiver = Receiver("tcp://localhost:5076", channel)

while True:
    data = receiver.recv()
    print(data)

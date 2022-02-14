from omnibus import Receiver
from graphic_interface import initGUI
import sys

# Take a channel as a command line argument. Defaults to all channels.
channel = ""
if len(sys.argv) > 1:
    channel = sys.argv[1]
receiver = Receiver(channel)

# Record the payload and time stamp of every message
# recieved.
samples = [
	[], []
]

def callback():
    while msg := receiver.recv_message(0):
        ## need to adjust for the format
        for sensor, data in msg.payload['data'].items():
            samples[0].append(msg.timestamp)
            samples[1].append(sum(data)/len(data))

        while len(samples[0]) > 50:
            samples[0].pop(0)
            samples[1].pop(0)

    return samples

initGUI(callback)

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
	##msg.timestamp, msg.payload
]

def callback():
    while msg := receiver.recv_message(0):
        ## need to adjust for the format
        for sensor, data in msg.payload['data'].items():
            samples.append([msg.timestamp, sum(data)/len(data)])
        if len(samples) > 50:
            samples.pop(0)

    return samples

initGUI(callback)

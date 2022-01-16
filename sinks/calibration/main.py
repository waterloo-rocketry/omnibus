from omnibus import Receiver
from graphic_interface import initGUI

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

while True:
    msg = receiver.recv_message()
    print(data)

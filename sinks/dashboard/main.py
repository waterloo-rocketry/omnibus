from omnibus import Receiver, server

import parsers
from dashboard import dashboard_driver

receiver = Receiver("")  # subscribe to all channels

networkReset = {
    "timeout": 3,
    "lastCheck": 0
}

def update():  # gets called every frame
    # read all the messages in the queue and no more (zero timeout)
    while msg := receiver.recv_message(0):
        # updates streams, which them updates the dashitems
        parsers.parse(msg.channel, msg.payload)
        networkReset["timeout"] = 3
    if networkReset["lastCheck"] <= 0:
        networkReset["lastCheck"] = 120
        # print("Timeout: " + str(networkReset["timeout"]))
        if (msg == None):
            networkReset["timeout"] -= 1
        if networkReset["timeout"] <= 0:
            receiver.reset()
            # print("Resetting...")
            networkReset["timeout"] = 3
    networkReset["lastCheck"] -= 1


dashboard_driver(update)

from omnibus import Receiver

import parsers
from dashboard import dashboard_driver

receiver: Receiver = Receiver("")  # subscribe to all channels


def update() -> None:  # gets called every frame
    # read all the messages in the queue and no more (zero timeout)
    while msg := receiver.recv_message(0):
        # updates streams, which them updates the dashitems
        parsers.parse(msg.channel, msg.payload)


dashboard_driver(update)

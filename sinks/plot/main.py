from omnibus import Receiver

from parsers import Parser
from dashboard import Dashboard

receiver = Receiver("")  # subscribe to all channels


def update():  # gets called every frame
    # read all the messages in the queue and no more (zero timeout)
    while msg := receiver.recv_message(0):
        # update whatever series subscribed to this channel
        Parser.all_parse(msg.channel, msg.payload)

Dashboard(update)

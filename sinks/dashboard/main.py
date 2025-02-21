from omnibus import Receiver
from omnibus.util import BuildInfoManager

import parsers
from dashboard import dashboard_driver

receiver = Receiver("")  # subscribe to all channels


def update():  # gets called every frame
    # read all the messages in the queue and no more (zero timeout)
    while msg := receiver.recv_message(0):
        # updates streams, which them updates the dashitems
        parsers.parse(msg.channel, msg.payload)

if __name__ == "__main__":
    bim = BuildInfoManager("Omnibus Dashboard")
    bim.print_startup_screen()
    bim.print_app_name()

dashboard_driver(update)


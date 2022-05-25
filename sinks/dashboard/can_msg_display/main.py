import sys

from pyqtgraph.Qt import QtWidgets

from omnibus import Receiver
from can_display import CanMessageDisplay
from ..parsers import Parser

receiver = Receiver("")  # subscribe to all channels


def update():
    while msg := receiver.recv_message(0):
        Parser.all_parse(msg.channel, msg.payload)


CanMessageDisplay(update)
# if __name__ == '__main__':
#     app = QtWidgets.QApplication(sys.argv)
#     # update()
#     display = CanMessageDisplay(update)
#     display.resize(800, 600)
#     display.show()

#     sys.exit(app.exec())

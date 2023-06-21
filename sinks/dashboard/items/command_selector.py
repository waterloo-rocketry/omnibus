from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QButtonGroup, QPushButton, QRadioButton
from pyqtgraph.Qt.QtGui import QPixmap
from pyqtgraph.parametertree.parameterTypes import FileParameter
from pyqtgraph.Qt.QtCore import QSize, Qt

from omnibus import Sender

from .dashboard_item import DashboardItem
from .registry import Register

CHANNEL_ROOT = "CAN/Commands"
COMMAND_DESTINATION = ""
sender = Sender()

DESTINATIONS = {
        "Umbillical": "",
        "Telemetry": "telemetry/",
}

def send_can_message(message):
    sender.send(COMMAND_DESTINATION + CHANNEL_ROOT, message)

@Register
class CommandSelector(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.group = QButtonGroup()
        self.buttons = []
        for i, name in enumerate(DESTINATIONS.keys()):
            b = QRadioButton(name)
            if i == 0:
                b.setChecked(True)
            self.buttons.append(b)
            self.group.addButton(b, i)
            self.layout.addWidget(b)
        self.group.buttonClicked.connect(self.clicked)


    def clicked(self, button):
        global COMMAND_DESTINATION
        i = self.group.id(button)
        COMMAND_DESTINATION = list(DESTINATIONS.values())[i]

    @staticmethod
    def get_name():
        return "Command Destination Selector"

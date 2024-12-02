import time
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QSlider,
    QPushButton
)

from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
from publisher import publisher


@Register
class TVCControllerSlider(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.widget_one = QSlider()
        self.widget_two = QSlider()

        self.send_button = QPushButton('SEND')
        self.send_button.clicked.connect(self.send_can_message)

        self.layout.addWidget(self.widget_one)
        self.layout.addWidget(self.widget_two)
        self.layout.addWidget(self.send_button)

    # whenever the SEND button (or equilvalent) is activated, pulse PyQT input widgets for visual feedback
    # and upon a successful CAN message encoding, emit the encoded message
    def send_can_message(self):
        try:
            actuator_value_1 = int(self.widget_one.value())
            actuator_value_2 = int(self.widget_two.value())
        except:
            print("Err")
            return


        can_message_1 = {
            'data': {
                'time': time.time(),
                'can_msg': {
                    'msg_type': 'ACTUATOR_CMD',
                    'board_id': 'ANY',
                    'time': 0,
                    'actuator': 'ACTUATOR_CHARGE_AIRBRAKE',
                    'req_state': actuator_value_1
                    },  # contains the message data bits
            }
        }

        can_message_2 = {
            'data': {
                'time': time.time(),
                'can_msg': {
                    'msg_type': 'ACTUATOR_CMD',
                    'board_id': 'ANY',
                    'time': 0,
                    'actuator': 'ACTUATOR_CHARGE_PAYLOAD',
                    'req_state': actuator_value_2
                    },  # contains the message data bits
            }
        }

        publisher.update('outgoing_can_messages', can_message_1)
        publisher.update('outgoing_can_messages', can_message_2)

    @staticmethod
    def get_name():
        return 'TVC controller slider'

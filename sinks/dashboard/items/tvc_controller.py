import time
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout
    QLineEdit,
    QPushButton,
)

from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
from publisher import publisher


@Register
class CanSender(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.widget_one = QLineEdit()
        self.widget_two = QLineEdit()

        self.send_button = QPushButton('SEND')
        self.send_button.clicked.connect(self.send_can_message)

        self.layout.addWidget(self.widget_one)
        self.layout.addWidget(self.widget_two)

    # whenever the SEND button (or equilvalent) is activated, pulse PyQT input widgets for visual feedback
    # and upon a successful CAN message encoding, emit the encoded message
    def send_can_message(self):
        can_message_1 = {
            'data': {
                'time': time.time(),
                'can_msg': {
                    'msg_type': 'ACTUATOR_CMD',
                    'board_id': 'ANY',
                    'time': 0,
                    'actuator': 1,
                    'req_state': int(3)
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
                    'actuator': 1,
                    'req_state': int(3)
                    },  # contains the message data bits
            }
        }

        publisher.update('outgoing_can_messages', can_message_1)
        publisher.update('outgoing_can_messages', can_message_2)

    @staticmethod
    def get_name():
        return 'TVC controller'

import time
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
)
from parsley.message_types import actuator_id
from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
from publisher import publisher


@Register
class TVCControllerEnable(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.status = False

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.button = QPushButton("Enable")
        self.button.clicked.connect(self.on_click)

        self.layout.addWidget(self.button)


    def on_click(self):
        self.status = not self.status
        self.button.setText("Disable" if self.status else "Enable")

        can_message = {
            'data': {
                'time': time.time(),
                'can_msg': {
                    'msg_prio': 'LOW',
                    'msg_type': 'ACTUATOR_CMD',
                    'board_type_id': 'ANY',
                    'board_inst_id': 'ANY',
                    'time': 1,
                    'actuator': 'ACTUATOR_TVC_ENABLE',
                    'cmd_state': 'ACTUATOR_ON' if self.status else 'ACTUATOR_OFF'
                    },
            }
        }

        publisher.update('outgoing_can_messages', can_message)


    # whenever the SEND button (or equilvalent) is activated, pulse PyQT input widgets for visual feedback
    # and upon a successful CAN message encoding, emit the encoded message
    @staticmethod
    def get_name():
        return 'TVC controller enable'

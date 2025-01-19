import time
import os
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QFileDialog,
    QPushButton,
    QLabel
)

from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
from publisher import publisher


@Register
class TVCControllerPreset(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.file = None

        self.file_input = QLabel("-")
        self.get_file_button = QPushButton('GET FILE')
        self.get_file_button.clicked.connect(self.get_file)


        self.send_button = QPushButton('START SEQUENCE')
        self.send_button.clicked.connect(self.send_sequence)

        self.layout.addWidget(self.file_input)
        self.layout.addWidget(self.get_file_button)
        self.layout.addWidget(self.send_button)

        self.msg_seq = []

    def get_file(self):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        save_directory = os.path.join(script_dir, "..", "..", "..", "sinks", "dashboard", "saved-files")
        (filename, _) = QFileDialog.getOpenFileName(self, "Open File", save_directory)
        self.file = filename
        self.file_input.setText(self.file)

    def send_sequence(self):
        self.send_button.setDisabled(True)

        self.msg_seq = []
        with open(self.file) as f:
            for line in f:
                arr  = line.strip().split(' ')

                if (len(arr) == 2):
                    v1, v2 = arr

                    can_message_1 = {
                        'data': {
                            'time': time.time(),
                            'can_msg': {
                                'msg_type': 'ACTUATOR_CMD',
                                'board_id': 'ANY',
                                'time': 0,
                                'actuator': 'ACTUATOR_CHARGE_AIRBRAKE',
                                'req_state': int(v1)
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
                                'req_state': int(v2)
                                },  # contains the message data bits
                        }
                    }
                    self.msg_seq.append((can_message_1, can_message_2))
                else:
                    self.msg_seq.extend([None] * int(arr[0]))

            publisher.subscribe_clock(1, self.on_clock_update)



    def on_clock_update(self, _):
        if len(self.msg_seq) == 0:
            publisher.unsubscribe_from_all(self.on_clock_update)
            self.send_button.setDisabled(False)
        elif (m := self.msg_seq.pop(-1)):
            m1, m2 = m
            publisher.update('outgoing_can_messages', m1)
            publisher.update('outgoing_can_messages', m2)



    @staticmethod
    def get_name():
        return 'TVC controller preset'

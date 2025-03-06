import time
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QHBoxLayout,
    QSlider,
    QLineEdit,
    QComboBox
)
from parsley.message_types import actuator_id
from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
from publisher import publisher


@Register
class TVCControllerActSlider(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.slider = QSlider()
        self.slider.setMinimum(-100)
        self.slider.setMaximum(100)
        self.text = QLineEdit()
        self.act_id_select = QComboBox()
        self.act_id_select.addItems(list(actuator_id.keys()))

        self.slider.valueChanged.connect(self.on_slider_change)
        self.text.textChanged.connect(self.on_text_change)

        self.layout.addWidget(self.act_id_select)
        self.layout.addWidget(self.slider)
        self.layout.addWidget(self.text)

    def on_text_change(self):
        try:
            val = int(self.text.text().strip())
        except:
            return
        act_id = self.act_id_select.currentText()

        self.slider.blockSignals(True)
        self.slider.setValue(val)
        self.slider.blockSignals(False)

        self.send_can_message(val, act_id)

    def on_slider_change(self, val):
        act_id = self.act_id_select.currentText()

        self.text.blockSignals(True)
        self.text.setText(str(val))
        self.text.blockSignals(False)

        self.send_can_message(val, act_id)


    # whenever the SEND button (or equilvalent) is activated, pulse PyQT input widgets for visual feedback
    # and upon a successful CAN message encoding, emit the encoded message
    def send_can_message(self, val, act_id):
        can_message = {
            'data': {
                'time': time.time(),
                'can_msg': {
                    'msg_prio': 'LOW',
                    'msg_type': 'ACTUATOR_ANALOG_CMD',
                    'board_type_id': 'ANY',
                    'board_inst_id': 'ANY',
                    'time': 1,
                    'actuator': act_id,
                    'cmd_state': val
                    },
            }
        }

        publisher.update('outgoing_can_messages', can_message)

    @staticmethod
    def get_name():
        return 'TVC controller act slider'

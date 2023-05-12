from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QCheckBox, QComboBox
from pyqtgraph.Qt.QtCore import Qt, QTimer

from .dashboard_item import DashboardItem
from .registry import Register

from omnibus import Sender
import time
import parsley.message_types as mt


@Register
class PeriodicCanSender(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        self.period = self.parameters.param('period').value()

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.check = QCheckBox()
        self.layout.addWidget(self.check)

        self.actuator_id = QComboBox()
        self.actuator_id.addItems(mt.actuator_id.keys())
        self.actuator_id.setFocusPolicy(Qt.StrongFocus)
        self.layout.addWidget(self.actuator_id)

        self.message_timer = QTimer()
        self.message_timer.timeout.connect(self.send_message)

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_widgets)
        self.pulse_count = 0
        self.pulse_period = 300  # ms

        self.sender = Sender()
        self.channel = 'CAN/Commands'

        self.parameters.param('period').sigValueChanged.connect(self.on_period_change)

    def add_parameters(self):
        period_param = {'name': 'period', 'type': 'int', 'value': 0}
        return [period_param]

    def send_message(self):
      if self.period == 0:
          self.message_timer.stop()
      else:
          can_message = {
              'data': {
                  'time': time.time(),
                  'can_msg': {
                      'msg_type': 'ACTUATOR_CMD',
                      'board_id': 'ANY',
                      'time': 0,
                      'actuator': self.actuator_id.currentText(),
                      'req_state': 'ACTUATOR_ON' if self.check.isChecked() else 'ACTUATOR_OFF'
                  }
              }
          }
          self.sender.send(self.channel, can_message)
          self.pulse_count = 2
          self.pulse_timer.start(self.pulse_period)
          
    def pulse_widgets(self):
        if self.pulse_count > 0:
            self.actuator_id.setDisabled(self.pulse_count % 2 == 0)
            self.pulse_count -= 1
        else:
            self.pulse_timer.stop()

          

    def on_period_change(self, _, value):
        self.period = value
        self.message_timer.start(self.period * 1000)

    @staticmethod
    def get_name():
        return "Periodic Can Sender"

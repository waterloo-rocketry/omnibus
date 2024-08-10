from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QCheckBox, QLabel, QRadioButton, QButtonGroup, QVBoxLayout
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.parametertree.parameterTypes import ListParameter
from .dashboard_item import DashboardItem
from .registry import Register
import time
import parsley.message_types as mt
from publisher import publisher


@Register
class PeriodicCanSender(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        self.parameters.param('period').setValue(0)

        self.period = self.parameters.param('period').value()
        self.actuator = self.parameters.param('actuator').value()

        # Specify the layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel(self.actuator)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 17px;")
        self.layout.addWidget(self.label)

        self.title = QLabel("Periodic CAN Sender")
        self.title.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title)
        self.status_label = QLabel("INACTIVE")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.status_label)

        self.radio_on = QRadioButton("ON")
        self.radio_off = QRadioButton("OFF")
        self.radio_off.setChecked(True)

        self.radio_on.clicked.connect(self.set_status)
        self.radio_off.clicked.connect(self.set_status)

        self.button_group = QButtonGroup(self)
        self.button_group.addButton(self.radio_on)
        self.button_group.addButton(self.radio_off)
        self.button_group.setExclusive(True)

        # Create a horizontal layout for the checkboxes
        self.h_layout = QHBoxLayout()
        self.h_layout.addWidget(self.radio_on)
        self.h_layout.addSpacing(20)
        self.h_layout.addWidget(self.radio_off)
        self.h_layout.setAlignment(Qt.AlignCenter)

        # Add the horizontal layout to the main vertical layout
        self.layout.addLayout(self.h_layout)

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_widgets)
        self.pulse_count = 0
        self.pulse_period = 300  # ms


        self.parameters.param('period').sigValueChanged.connect(self.on_period_change)
        self.parameters.param('actuator').sigValueChanged.connect(self.on_actuator_change)

        self.last_time = time.time()
        publisher.subscribe("ALL", self.on_data_update)

    def on_data_update(self, _, __):
        self.cur_time = time.time()
        time_elapsed = self.cur_time - self.last_time
        # send the can message if enough time has passed
        if time_elapsed > self.period and self.period != 0:
            can_message = {
                'data': {
                    'time': time.time(),
                    'can_msg': {
                        'msg_type': 'ACTUATOR_CMD',
                        'board_id': 'ANY',
                        'time': 0,
                        'actuator': self.actuator,
                        'req_state': 'ACTUATOR_ON' if self.radio_on.isChecked() else 'ACTUATOR_OFF'
                    },

                }
            }
            publisher.update('outgoing_can_messages', can_message)
            self.pulse_count = 2
            self.pulse_timer.start(self.pulse_period)
            self.last_time = self.cur_time

    def add_parameters(self):
        actuator_ids = list(mt.actuator_id.keys())
        series_param = ListParameter(name='actuator', type='list',
                                     default=actuator_ids[0], limits=actuator_ids)
        period_param = {'name': 'period', 'type': 'int', 'value': 0, 'limits': (0, None)}
        return [series_param, period_param]
        

    def pulse_widgets(self):
        if self.pulse_count > 0:
            if self.period != 0 and self.pulse_count % 2 == 0:
                if self.radio_on.isChecked():
                    self.setStyleSheet("background-color: green;")
                else:
                    self.setStyleSheet("background-color: red;")
            else:
                self.setStyleSheet("")
            self.pulse_count -= 1
        else:
            self.pulse_timer.stop()

    def set_status(self):
        if self.period != 0:
            self.status_label.setText("ACTIVE")
        elif self.period == 0:
            self.status_label.setText("INACTIVE")

    def on_period_change(self, _, value):
        if value >= 0:
            self.period = value
        else:
            self.period = 0  # Set the period to 0 if the value is less than 0
        self.set_status()

    def on_actuator_change(self, _, value):
        self.actuator = value
        self.label.setText(self.actuator)

    @staticmethod
    def get_name():
        return "Periodic CAN Sender"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

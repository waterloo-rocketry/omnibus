from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QCheckBox
from pyqtgraph.Qt.QtCore import QTimer
from pyqtgraph.parametertree.parameterTypes import ListParameter

from .dashboard_item import DashboardItem
from .registry import Register
from .command_selector import send_can_message

import parsley.fields as pf
from parsley.message_definitions import CAN_MESSAGE

import time
from parsers import publisher


@Register
class GenericPeriodicCanSender(DashboardItem):
    def __init__(self, *args):
        self.msg_types = list(CAN_MESSAGE.get_keys())
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.setStyleSheet("background-color: blue")

        self.check = QCheckBox()
        self.layout.addWidget(self.check)

        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.pulse_widgets)
        self.pulse_count = 0
        self.pulse_period = 300  # ms

        self.last_time = time.time()
        publisher.subscribe("ALL", self.on_data_update)

    def on_data_update(self, _, __):
        self.cur_time = time.time()
        time_elapsed = self.cur_time - self.last_time

        # get all parameters on the period can sender and arrange them in a dictionary
        msg_parameters = {param: self.parameters.param(param).value() for param in list(self.parameters.getValues())}

        # remove parameters that aren't required in the msg
        period = msg_parameters.pop('period')
        msg_parameters.pop('width')
        msg_parameters.pop('height')

        # send the can message if enough time has passed and if checkbox is checked
        if self.check.isChecked() and time_elapsed > period and period != 0:
            can_message = {
                'data': {
                    'time': time.time(),
                    'can_msg': msg_parameters
                }
            }
            send_can_message(can_message)
            self.pulse_count = 2
            self.pulse_timer.start(self.pulse_period)
            self.last_time = self.cur_time

    def add_parameters(self):
        # we avoid using the default `add_parameters` function as all the parameters will be updated
        #   when msg_type updates anyway. instead we use `set_parameters_by_msg_type` and initalize to the first msg_type
        self.set_parameters_by_msg_type(self.msg_types[0])

        return []

    def pulse_widgets(self):
        if self.pulse_count > 0:
            if self.pulse_count % 2 == 0:
                self.setStyleSheet("background-color: black;")
            else:
                self.setStyleSheet("background-color: blue")
            self.pulse_count -= 1
        else:
            self.pulse_timer.stop()

    def set_parameters_by_msg_type(self, msg_type):
        '''
            Sets the parameters of the periodic_can_sender based on the msg_type.
            Parameters will always contain `width`, `height`, `period`, and `msg_type` and the rest are filled in
                based on the `msg_type`
        '''
        
        # the first time this method is called period won't be defined
        old_parameters = list(self.parameters.getValues())
        period = 0
        if 'period' in old_parameters:
            period = self.parameters.param('period').value()

        default_required_parameters = [
            self.parameters.param('width'),
            self.parameters.param('height'),
            {"name": "period", "type": "int", "value": period},
            ListParameter(
                name='msg_type',
                type='list',
                value=msg_type,
                limits=self.msg_types
            )
        ]

        msg_type_specific_parameters = []

        fields_for_msg_type = list(CAN_MESSAGE.get_fields(msg_type))
        for field in fields_for_msg_type:
            match type(field):
                case pf.Enum | pf.Switch:
                    msg_type_specific_parameters.append(ListParameter(
                        name=field.name,
                        type='list',
                        default=list(field.get_keys())[0],
                        limits=list(field.get_keys())
                    ))
                case pf.ASCII:
                    msg_type_specific_parameters.append({
                        'name': field.name,
                        'type': 'str',
                        'value': '',
                    })
                case pf.Numeric:
                    msg_type_specific_parameters.append({
                        'name': field.name,
                        'type': 'int',
                        'value': 0
                    })

        # replace parameters with defaults + msg_type specifics
        self.parameters.clearChildren();
        self.parameters.addChildren(default_required_parameters + msg_type_specific_parameters);

        # set update function on msg_type (all other params have a generic handler built in)
        self.parameters.param('msg_type').sigValueChanged.connect(self.on_msg_type_update)

    def on_msg_type_update(self, target, msg_type):
        self.set_parameters_by_msg_type(msg_type)

    @staticmethod
    def get_name():
        return "Generic Periodic Can Sender"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

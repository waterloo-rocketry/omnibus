from math import ceil, log, log10, log2
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer, QObject, Signal, QEvent
from pyqtgraph.Qt.QtGui import (
    QColor,
    QPalette,
    QRegularExpressionValidator,
    QCursor
)
from pyqtgraph.Qt.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListView,
    QApplication
)

import parsley.fields as pf
from parsley.message_definitions import CAN_MSG
from parsley.bitstring import BitString
# from omnibus import Sender
# from parsers import publisher
from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker
@Register
class CanSender(DashboardItem):
    """
    Visual blueprint of the CanSender dashboard item:
                  
    |-------------------------------------------------------------|
    | msg_type | board_id | time             | command |          | <- field names
    |----------|----------|------------------|---------|----------|
    | Dropdown | Dropdown | 24-bit Textfield | Dropdown|   Send   | <- field-dependent widgets to gather input
    |-------------------------------------------------------------|

    - Dropdowns contain a field's dictionary keys
        => when a Switch is encountered, populate the first key's fields
    - Text fields contain two different input masks:
        => Numerics: only hexadecimal values (TODO: I think user-input should be post-scaled but would need a way to communicate that)
        => ASCII: any string
    - Upon pressing send:
        => for every field that fails to encode its data, pulse the field in quick successions (comfy red)
        => if every field successfully encodes its data, long pulse all of the fields once (comfy green)
    - Width of CanSender widget scales depending on the CAN message length (TODO)
    """

    def __init__(self, props):
        """
        Coding checklist:
        - text field signal
            => check if after entering this character, the text field is maxed out, then move cursor/highlight the next field
            => check if backspace, might need to move cursor/highlight the previous field
        - dropdown signal
            => TODO: check if you can unselect your option (would be equilvalent to our intial base case)
            => on change, reconstruct all the items preceeding the dropdown
                ++ need to apply all the input masks and signal event handlers during runtime
                ++ avoid touching data to the left of the dropdown
        - button signal
            => verify every field's data can be properly encoded (wrap in try catch)
            => pulse the apppropriate color for the fields
            => possibly send the data over
        
        """
        super().__init__()
        # self.canlib_info = CanlibMetadata("can_sender_data.txt")
        # self.omnibus_sender = Sender()
        # self.channel = "CAN/Commands"

        self.initialize_variables()

    def initialize_variables(self):
        self.layout_manager = QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.text_signals = EventTracker()
        self.text_signals.backspace_pressed.connect(self.try_move_cursor_backwards)

        self.numeric_mask = "[\-0-9]" # not sure if we want to stick with base 16 or base 10 (how to deal with scaled?)
        self.ascii_mask = "[\x00-\x7F]"

        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse_fields)
        self.pulse_indexes = []

        # i dont want to constantly create/delete widgets from my arrays, so I'll use the idea
        # of an array-implemented stack where you 'delete' by moving your index pointer
        self.fields = [None] * 16
        self.widgets = [None] * 16
        self.widget_labels = [None] * 16
        self.widget_index = -1
        self.widget_to_index = {}

        self.add_fields([CAN_MSG])
        self.send_button = self.create_send_button()
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index + 1)

        # constants
        self.INVALID_NUM_PULSES = 3 # number of pulses to display when a Field throws an error
        self.INVALID_PULSE_PERIOD = 100 # period (ms) between each pulse
        self.VALID_NUM_PULSES = 1
        self.VALID_PULSE_PERIOD = 500

    def add_fields(self, fields: List[pf.Field]):
        for field in fields:
            self.widget_index += 1
            if isinstance(field, pf.Switch) or isinstance(field, pf.Enum):
                dropdown = QComboBox()
                dropdown.setMinimumContentsLength(20) # TODO: I swear this changed the height of row entries but I mgiht be capping
                dropdown_items = list(field.get_keys())
                dropdown.addItems(dropdown_items)
                dropdown.view().setViewMode(QListView.ListMode)
                self.widgets[self.widget_index] = dropdown
            elif isinstance(field, pf.Numeric) or isinstance(field, pf.ASCII):
                mask = self.numeric_mask if isinstance(field, pf.Numeric) else self.ascii_mask
                data_length = self.get_field_length(field)
                textfield = QLineEdit()
                textfield.setAlignment(Qt.AlignCenter)
                textfield.setValidator(QRegularExpressionValidator(data_length * mask))
                textfield.setPlaceholderText(data_length * "0")
                textfield.installEventFilter(self.text_signals)
                textfield.textChanged.connect(self.try_move_cursor_forwards)
                self.widgets[self.widget_index] = textfield

            label = QLabel(field.name)
            label.setWordWrap(True) # i used to have this, check if still needed

            self.fields[self.widget_index] = field
            self.widget_labels[self.widget_index] = label
            self.widget_to_index[self.widgets[self.widget_index]] = self.widget_index # create mapping between widget and its index in the can message

            self.layout_manager.addWidget(self.widget_labels[self.widget_index], 0, self.widget_index) # TODO: create dynamic widget width based on field bit length
            self.layout_manager.addWidget(self.widgets[self.widget_index], 1, self.widget_index) # TODO: create dynamic widget width based on fieldbit length
            if isinstance(field, pf.Switch):
                self.widgets[self.widget_index].currentTextChanged.connect(self.update_can_msg)
                nested_fields = field.get_fields(dropdown_items[0]) # display the first Switch row to show something
                self.add_fields(nested_fields)

    def update_can_msg(self, text):
        dropdown = self.sender()
        dropdown_index = self.widget_to_index[dropdown]

        # delete the widgets from [dropdown_index + 1, self.widget_index] from layout manager
        for index in range(dropdown_index + 1, self.widget_index + 1):
            widget = self.widgets[index]
            label = self.widget_labels[index]
            # remove widget from layout manager
            self.layout_manager.removeWidget(widget)
            self.layout_manager.removeWidget(label)
            # remove widget from memory
            widget.deleteLater()
            label.deleteLater()
        # remove send button
        self.layout_manager.removeWidget(self.send_button)
        self.send_button.deleteLater()

        # insert the new widgets
        self.widget_index = dropdown_index
        switch_field = self.fields[self.widget_index]
        nested_fields = switch_field.get_fields(text)
        self.add_fields(nested_fields)
        # bring back the send button
        self.send_button = self.create_send_button()
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index + 1)

    def send_can_message(self):
        bit_str = self.parse_can_msg()

        if bit_str == None:
            return
        self.pulse_indexes = [i for i in range(0, self.widget_index + 1)]
        self.pulse(invalid=False)
        # self.omnibus_sender.send(self.channel, self.parse_data())

    def parse_can_msg(self):
        self.pulse_indexes = []
        bit_str = BitString()
        for index in range(0, self.widget_index + 1):
            widget = self.widgets[index]
            field = self.fields[index]
            text = widget.text() if isinstance(widget, QLineEdit) else widget.currentText()
            try:
                if isinstance(field, pf.Numeric):
                    text = int(text)
                bit_str.push(*field.encode(text))
            except Exception as e:
                print(f"{field.name} | {e}")
                self.pulse_indexes.append(index)

        if self.pulse_indexes:
            self.pulse(invalid=True)

        return None if self.pulse_indexes else bit_str

    def pulse(self, invalid):
        self.pulse_count = 0
        self.invalid = invalid
        pulse_period = self.INVALID_PULSE_PERIOD if invalid else self.VALID_PULSE_PERIOD
        self.timer.start(pulse_period)

    def pulse_fields(self):
        pulse_frq = self.INVALID_NUM_PULSES if self.invalid else self.VALID_NUM_PULSES
        if self.pulse_count < 2*pulse_frq:
            for index in self.pulse_indexes:
                widget = self.widgets[index]
                widget.setDisabled(self.pulse_count%2 == 0)
            self.pulse_count += 1
        else:
            self.timer.stop()

    def get_field_length(self, field: pf.Field) -> int:
        match type(field):
            case pf.ASCII:
                return field.length // 8
            case pf.Numeric:
                minus_sign = 1 if field.signed else 0
                return minus_sign + ceil(field.length * log10(2))
            case _:
                return -1

    def create_send_button(self):
        button = QPushButton("SEND")
        button.clicked.connect(self.send_can_message)
        return button

    def try_move_cursor_forwards(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
        field = self.fields[index]
        data_length = self.get_field_length(field)
        text_length = len(widget.text())

        if text_length == data_length:
            next_index = min(self.widget_index, index + 1)
            next_widget = self.widgets[next_index]
            next_widget.setFocus()

    def try_move_cursor_backwards(self, widget):
        index = self.widget_to_index[widget]
        text_length = len(widget.text())

        if text_length == 0:
            previous_index = max(0, index - 1)
            previous_widget = self.widgets[previous_index]
            previous_widget.setText(previous_widget.text()[:-1])
            previous_widget.setFocus()

    def get_name():
        return "CAN Sender"

    def get_props(self):
        return True

    def on_delete(self):
        pass

    def prompt_for_properties(self):
        return True

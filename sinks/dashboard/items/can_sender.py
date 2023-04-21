from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics
from pyqtgraph.Qt.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton
)

import parsley.fields as pf
from parsley.message_definitions import CAN_MSG
from parsley.bitstring import BitString
from omnibus import Sender
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
    | Dropdown | Dropdown | 24-bit text_field| Dropdown|   Send   | <- field-dependent widgets to take user input
    |-------------------------------------------------------------|

    - Dropdowns contain a field's dictionary keys
        => when a Switch is encountered, populate the first key's fields
    - Text fields contain two different input masks:
        => Numerics: only numbers
        => ASCII: any string
    - Upon pressing send:
        => for every field that fails to encode its data, pulse the field in quick succession
        => if every field successfully encodes its data, long pulse all of the fields once
    """

    def __init__(self, props):
        super().__init__()
        # constants
        self.INVALID_NUM_PULSES = 3 # number of pulses to display when a Field throws an error
        self.INVALID_PULSE_PERIOD = 100 # period (ms) between each pulse
        self.VALID_NUM_PULSES = 1
        self.VALID_PULSE_PERIOD = 500
        self.WIDGET_TEXT_PADDING = 50 # pixels

        # use grid layout so that widgets can be placed in a grid
        self.layout_manager = QGridLayout(self)
        self.setLayout(self.layout_manager)

        # track backspace key presses to move the cursor backwards when the current textfield is empty
        self.text_signals = EventTracker()
        self.text_signals.backspace_pressed.connect(self.try_move_cursor_backwards)

        # text field RegEx input mask
        self.numeric_mask = "[\.\-0-9]" # allows numbers, periods, minus sign
        self.ascii_mask = "[\x00-\x7F]" # allows all ASCII characters

        # preallocate the size of the arrays since the length of a CAN message is dynamic
        self.fields = [None] * 16 # parsley field
        self.widgets = [None] * 16 # PyQT widget
        self.widget_labels = [None] * 16 # PyQT label
        self.widget_index = -1 # index of the right-most widget
        self.widget_to_index = {} # map to associate widgets to their index

        # display contents onto the dashboard item
        self.display_can_fields([CAN_MSG])
        self.create_send_button()

        # when a button is pressed, pulse widgets for visual feedback
        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse_widgets)
        self.pulse_indexes = []

        # when a button is pressed, try to send the message out
        self.omnibus_sender = Sender()
        self.channel = "CAN/Commands"

    def display_can_fields(self, fields: List[pf.Field]):
        for field in fields:
            self.widget_index += 1
            if isinstance(field, pf.Switch) or isinstance(field, pf.Enum):
                dropdown_items = list(field.get_keys())
                dropdown_max_length = max(len(item) for item in dropdown_items)

                dropdown = QComboBox()
                dropdown.addItems(dropdown_items)
                max_width = self.get_widget_text_width(dropdown, dropdown_max_length)
                dropdown.setFixedWidth(max_width + self.WIDGET_TEXT_PADDING)
                # unfortuantely on Macs, you aren't able to customize the dropdown, which means
                # you cant scroll the contents (it'll be one huge list)
                # see: https://doc.qt.io/qt-5/qcombobox.html#maxVisibleItems-prop
                dropdown.setMaxVisibleItems(15)
                dropdown.setFocusPolicy(Qt.StrongFocus) # display the blue border when widget is focused
                self.widgets[self.widget_index] = dropdown
            elif isinstance(field, pf.Numeric) or isinstance(field, pf.ASCII):
                mask = self.numeric_mask if isinstance(field, pf.Numeric) else self.ascii_mask
                data_length = self.get_field_length(field)

                text_field = QLineEdit()
                max_width = self.get_widget_text_width(text_field, data_length)
                text_field.setFixedWidth(max_width + self.WIDGET_TEXT_PADDING)
                text_field.setAlignment(Qt.AlignCenter)
                text_field.setValidator(QRegularExpressionValidator(data_length * mask))
                text_field.setPlaceholderText(data_length * "0")
                text_field.installEventFilter(self.text_signals)
                # when a textfield is full, move the cursor forwards to the next widget
                text_field.textChanged.connect(self.try_move_cursor_forwards)
                text_field.setFocusPolicy(Qt.StrongFocus) # display the blue border when widget is focused
                self.widgets[self.widget_index] = text_field

            # if the field comes with a unit, display it in brackets
            label_text = f"{field.name} ({field.unit})" if field.unit else field.name
            label = QLabel(label_text)
            label.setWordWrap(True)

            self.fields[self.widget_index] = field
            self.widget_labels[self.widget_index] = label
            # create a mapping between widget and its index in the can message
            self.widget_to_index[self.widgets[self.widget_index]] = self.widget_index
            self.layout_manager.addWidget(self.widget_labels[self.widget_index], 0, self.widget_index)
            self.layout_manager.addWidget(self.widgets[self.widget_index], 1, self.widget_index)

            if isinstance(field, pf.Switch):
                self.widgets[self.widget_index].currentTextChanged.connect(self.update_can_msg)
                nested_fields = field.get_fields(dropdown_items[0]) # display first row's contents
                self.display_can_fields(nested_fields)

    def update_can_msg(self, text: str):
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
        self.display_can_fields(nested_fields)
        # bring back the send button
        self.create_send_button()

    def send_can_message(self):
        bit_str = self.parse_can_msg()

        if bit_str == None:
            return
        # if every field successfully encoded its data, long pulse all of the fields once
        self.pulse_indexes = [i for i in range(0, self.widget_index + 1)]
        self.pulse(pulse_invalid=False)
        message = {
            "data": bit_str.data,
            "length": bit_str.length
        }
        self.omnibus_sender.send(self.channel, message)

    def parse_can_msg(self):
        self.pulse_indexes = []
        bit_str = BitString()
        for index in range(0, self.widget_index + 1):
            widget = self.widgets[index]
            field = self.fields[index]
            text = widget.text() if isinstance(widget, QLineEdit) else widget.currentText()
            try:
                if isinstance(field, pf.Numeric):
                    text = float(text)
                bit_str.push(*field.encode(text))
            except Exception as e:
                print(f"{field.name} | {e}")
                self.pulse_indexes.append(index)

        if self.pulse_indexes:
            self.pulse(pulse_invalid=True)

        return None if self.pulse_indexes else bit_str

    def pulse(self, pulse_invalid: bool):
        self.pulse_count = 0
        self.invalid = pulse_invalid
        pulse_period = self.INVALID_PULSE_PERIOD if pulse_invalid else self.VALID_PULSE_PERIOD
        self.timer.start(pulse_period)

    def pulse_widgets(self):
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

    def get_widget_text_width(self, widget, max_chars: int):
        font_metrics = QFontMetrics(widget.font())
        text_width = font_metrics.boundingRect('X' * max_chars).width()
        return text_width

    def create_send_button(self):
        self.send_button = QPushButton("SEND")
        max_width = self.get_widget_text_width(self.send_button, 4)
        self.send_button.setFixedWidth(max_width + self.WIDGET_TEXT_PADDING)
        self.send_button.setFocusPolicy(Qt.TabFocus)
        self.send_button.clicked.connect(self.send_can_message)
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index + 1)

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
            previous_widget.setFocus()
            if isinstance(previous_widget, QLineEdit):
                previous_widget.setText(previous_widget.text()[:-1])

    def get_name():
        return "CAN Sender"

    def get_props(self):
        return True

    def on_delete(self):
        pass

    def prompt_for_properties(self):
        return True

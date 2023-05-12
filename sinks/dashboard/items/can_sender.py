import time
from math import ceil, log10
from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QRegularExpressionValidator, QFontMetrics, QFont
from pyqtgraph.Qt.QtWidgets import (
    QComboBox,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy
)

import parsley.fields as pf
from parsley.message_definitions import CAN_MESSAGE
from omnibus import Sender
from .registry import Register
from .dashboard_item import DashboardItem
from utils import EventTracker


@Register
class CanSender(DashboardItem):
    """
    Visual blueprint of the CanSender dashboard item:

    |---------------------------------------------------------------|
    | msg_type | board_id | time (seconds)    | command  |          | <- field names (conditional: unit in brackets)
    |----------|----------|-------------------|----------|----------|
    | Dropdown | Dropdown | 24-bit text_field | Dropdown |   Send   | <- field-dependent widgets to take input
    |----------|----------|-------------------|----------|----------|
    |          |          | Parsley error     |          |          | <- (conditional: parsley encoding error)
    |---------------------------------------------------------------|

    - Dropdowns contain a field's dictionary keys
        => when a Switch is encountered, populate the first key's fields
    - Text fields contain two different input masks:
        => Numerics: only numbers
        => ASCII: all ASCII characters
    - Upon pressing send:
        => for every field that fails to encode its data, pulse said field in quick succession and display the parsley error
        => if every field successfully encodes its data, long pulse all of the fields once and emit the message to CAN/commands
    """

    def __init__(self, *args):
        super().__init__(*args)
        # constants
        self.INVALID_PULSES = 3  # number of pulses to display when a field fails to encode data
        self.INVALID_PULSE_PERIOD = 100  # ms
        self.VALID_PULSES = 1
        self.VALID_PULSE_PERIOD = 500
        self.WIDGET_TEXT_PADDING = 50  # pixels

        # using grid layout since widgets are designed in a grid-like format
        self.layout_manager = QGridLayout(self)
        self.setLayout(self.layout_manager)

        # tracks backspace presses to move the cursor backwards when the current textfield is empty
        self.text_signals = EventTracker()
        self.text_signals.backspace_pressed.connect(self.try_move_cursor_backwards)

        # tracks enter/return presses to send the CAN message (equilvalent to clicking the send button)
        # need to install the event filter on the dashboard widget since whenever the dashboard widget
        # is in focus, we want to be able to send the CAN message
        self.send_signals = EventTracker()
        self.send_signals.enter_pressed.connect(self.send_can_message)
        self.installEventFilter(self.send_signals)

        # text field regular expression input mask (won't accept characters not defined here)
        self.numeric_mask = '[\.\-0-9]'  # allows numbers, periods, and minus sign
        self.ascii_mask = '[\x00-\x7F]'  # allows all ASCII characters

        # preallocate the arrays since the length of a CAN message is dynamic
        self.fields = [None] * 16  # stores the parsley fields
        self.widgets = [None] * 16  # stores the PyQT input widgets
        self.widget_widths = [None] * 16  # tracks the width of each column
        # stores the PyQT labels describing the parsley field names
        self.widget_labels = [None] * 16
        self.widget_error_labels = [None] * 16  # displays parsley field encoding errors
        self.widget_index = -1  # index of the right-most PyQT widget
        self.widget_to_index = {}  # associates widgets to their parsley can message index

        # display the first can message
        self.display_can_fields([CAN_MESSAGE])
        self.create_send_button()

        # when a button is pressed, pulse widgets for visual feedback
        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse_widgets)
        self.pulse_indices = []

        # when a button is pressed and everything is valid, send the message out
        self.omnibus_sender = Sender()
        self.channel = 'CAN/Commands'

    # displays PyQT input widgets for a given CAN message
    def display_can_fields(self, fields: List[pf.Field]):
        self.clear_error_messages()  # remove any preexisiting error lables
        for field in fields:
            self.widget_index += 1
            if isinstance(field, pf.Switch) or isinstance(field, pf.Enum):
                dropdown_items = list(field.get_keys())
                dropdown_max_length = max(len(item) for item in dropdown_items)

                dropdown = QComboBox()
                dropdown.addItems(dropdown_items)
                # unfortunately on Mac, you aren't able to customize the dropdown which means that
                # you can't hover and scroll over the contents (it'll be one huge list when expanded)
                # see: https://doc.qt.io/qt-5/qcombobox.html#maxVisibleItems-prop
                dropdown.setMaxVisibleItems(15)
                dropdown.setFocusPolicy(Qt.StrongFocus)  # allows tabbing between widgets
                # calculate the width of the widget
                max_text_width = self.get_widget_text_width(dropdown, dropdown_max_length)
                self.widget_widths[self.widget_index] = max_text_width + self.WIDGET_TEXT_PADDING
                dropdown.setFixedWidth(self.widget_widths[self.widget_index])
                self.widgets[self.widget_index] = dropdown
            elif isinstance(field, pf.Numeric) or isinstance(field, pf.ASCII):
                mask = self.numeric_mask if isinstance(field, pf.Numeric) else self.ascii_mask
                data_length = self.get_field_length(field)

                text_field = QLineEdit()
                text_field.setAlignment(Qt.AlignCenter)
                text_field.setValidator(QRegularExpressionValidator(data_length * mask))
                text_field.setPlaceholderText(data_length * '0')
                text_field.installEventFilter(self.text_signals)
                # when a textfield is full, move the cursor forwards to the next widget
                text_field.textChanged.connect(self.try_move_cursor_forwards)
                text_field.setFocusPolicy(Qt.StrongFocus)  # allows tabbing between widgets
                # calculate the width of the widget
                max_text_width = self.get_widget_text_width(text_field, data_length)
                self.widget_widths[self.widget_index] = max_text_width + self.WIDGET_TEXT_PADDING
                text_field.setFixedWidth(self.widget_widths[self.widget_index])
                self.widgets[self.widget_index] = text_field

            # if the field comes with a unit, display it in brackets
            label_text = f'{field.name} ({field.unit})' if field.unit else field.name
            label = QLabel(label_text)
            label.setWordWrap(True)
            label.setFixedWidth(self.widget_widths[self.widget_index])

            self.fields[self.widget_index] = field
            self.widget_labels[self.widget_index] = label
            # create a mapping between widget and its index in the can message
            self.widget_to_index[self.widgets[self.widget_index]] = self.widget_index
            self.layout_manager.addWidget(
                self.widget_labels[self.widget_index], 0, self.widget_index)  # add widget to first row
            self.layout_manager.addWidget(
                self.widgets[self.widget_index], 1, self.widget_index)  # add widget to second row

            # if the current parsley field is a Switch (aka it contains nested CAN messages),
            # then display the first row's parsley fields
            if isinstance(field, pf.Switch):
                self.widgets[self.widget_index].currentTextChanged.connect(self.update_can_msg)
                nested_fields = field.get_fields(dropdown_items[0])
                self.display_can_fields(nested_fields)

    # recreates the necessary PyQT input widgets whenever a parsley Switch field changes value
    def update_can_msg(self, text: str):
        dropdown = self.sender()  # get the specific dropdown that had it's value changed
        dropdown_index = self.widget_to_index[dropdown]

        # delete the PyQT widgets from [dropdown_index + 1, self.widget_index) from layout manager
        for index in range(dropdown_index + 1, self.widget_index):
            widget = self.widgets[index]
            label = self.widget_labels[index]
            label.setText('')
            # remove widget from layout manager
            self.layout_manager.removeWidget(widget)
            # remove widget from memory
            widget.deleteLater()
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

    # whenever the SEND button (or equilvalent) is activated, pulse PyQT input widgets for visual feedback
    # and upon a successful CAN message encoding, emit the encoded message
    def send_can_message(self):
        try:
            can_message = {
                'data': {
                    'time': time.time(),
                    'can_msg': self.parse_can_msg()  # contains the message data bits
                }
            }
            self.omnibus_sender.send(self.channel, can_message)
            self.pulse_indices = list(range(self.widget_index))
            self.pulse()
        except ValueError:
            # ValueError is something that is thrown in parsley encoding, but
            # its common enough that it might happen elsewhere so just in case
            # ensure that something is pulsing upon an error
            if not self.pulse_indices:
                self.pulse_indices = list(range(self.widget_index))
            self.pulse(pulse_invalid=True)

    # attempts to encode the PyQT input widgets and, if the encoding is unsuccessful, raises a ValueError
    def parse_can_msg(self) -> dict:
        # reset any existing information
        self.pulse_indices = []
        self.clear_error_messages()

        parsed_data = {}
        for index in range(self.widget_index):
            widget = self.widgets[index]
            field = self.fields[index]
            text = widget.text() if isinstance(widget, QLineEdit) else widget.currentText()
            try:
                if isinstance(field, pf.Numeric):
                    text = float(text)
                field.encode(text)  # if there is an encoding error, the error will be caught
                parsed_data[field.name] = text
            except (ValueError, IndexError) as error:
                self.pulse_indices.append(index)
                self.display_error_message(index, str(error))

        if self.pulse_indices:
            raise ValueError
        return parsed_data

    # visually pulse the PyQT input widgets whenever the SEND button (or equilvalent) is activated
    def pulse(self, pulse_invalid=False):
        if pulse_invalid:
            pulse_period = self.INVALID_PULSE_PERIOD
            pulse_frq = self.INVALID_PULSES
        else:
            pulse_period = self.VALID_PULSE_PERIOD
            pulse_frq = self.VALID_PULSES
        self.pulse_count = 2 * pulse_frq
        self.timer.start(pulse_period)

    # when QTimer starts, this function is periodically called until QTimer stops
    def pulse_widgets(self):
        if self.pulse_count > 0:
            for index in self.pulse_indices:
                widget = self.widgets[index]
                widget.setDisabled(self.pulse_count % 2 == 0)
            self.pulse_count -= 1
        else:
            self.timer.stop()

    def clear_error_messages(self):
        for label in self.widget_error_labels:
            if label == None:
                continue
            label.setText('')

    # creates a label describing the parsley encoding error
    def display_error_message(self, index: int, message: str):
        label = QLabel(message)
        label.setWordWrap(True)  # allow text to wrap around
        label.setFont(QFont(label.font().family(), 10))
        label.setFixedWidth(self.widget_widths[index])
        # allow label to expand vertically as much as needed
        label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)
        self.widget_error_labels[index] = label
        # add the widget to the 3rd row
        self.layout_manager.addWidget(self.widget_error_labels[index], 2, index)

    # returns an estimated upperbound on the input-able length of a field as a safety net
    def get_field_length(self, field: pf.Field) -> int:
        match type(field):
            case pf.ASCII:
                return field.length // 8
            case pf.Numeric:
                # we want to define an upper bound for the length but decimals can be
                # infintely long so assume 3 decimal digits + period = 4 characters only if
                # there is a defined scale multipler, which probably indicates a floating point
                minus_sign = 1 if field.signed else 0
                # number of digits to contain a binary lengthed number
                integer = ceil(log10(2**field.length))
                decimals = 4 if field.scale != 1 else 0
                return minus_sign + integer + decimals
            case _:
                return -1

    # calculate the text width of max_char characters given a widget's choice of font
    def get_widget_text_width(self, widget, max_chars: int) -> int:
        font_metrics = QFontMetrics(widget.font())
        text_width = font_metrics.boundingRect('X' * max_chars).width()
        return text_width

    # its hard to move a widget in a layout manager, so remove and recreate the SEND button
    def create_send_button(self):
        self.widget_index += 1
        self.send_button = QPushButton('SEND')
        max_text_width = self.get_widget_text_width(self.send_button, max_chars=4)
        self.send_button.setFixedWidth(max_text_width + self.WIDGET_TEXT_PADDING)
        self.send_button.setFocusPolicy(Qt.TabFocus)
        self.send_button.clicked.connect(self.send_can_message)
        # add the button to the 2nd row
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index)

    # moves the cursor to the next input widget if the current textfield is full
    def try_move_cursor_forwards(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
        field = self.fields[index]
        data_length = self.get_field_length(field)
        text_length = len(widget.text())

        if text_length == data_length:
            # self.widget_index refers to the send button, so the
            # last focusable widget is the one before it
            next_index = min(self.widget_index - 1, index + 1)
            next_widget = self.widgets[next_index]
            next_widget.setFocus()

    # moves the cursor to the previous input widget if the current textfield is empty
    def try_move_cursor_backwards(self, widget):
        index = self.widget_to_index[widget]
        text_length = len(widget.text())

        if text_length == 0:
            previous_index = max(0, index - 1)
            previous_widget = self.widgets[previous_index]
            previous_widget.setFocus()
            if isinstance(previous_widget, QLineEdit):
                # backspace was pressed and the current textfield is empty, so
                # remove a character from the previous textfield
                previous_widget.setText(previous_widget.text()[:-1])

    @staticmethod
    def get_name():
        return 'CAN Sender'

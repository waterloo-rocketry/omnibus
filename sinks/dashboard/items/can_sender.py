from typing import List
from pyqtgraph.Qt.QtCore import Qt, QTimer, QObject, Signal, QEvent
from pyqtgraph.Qt.QtGui import (
    QColor,
    QPalette,
    QRegularExpressionValidator
)
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
# from omnibus import Sender
# from parsers import publisher
from .registry import Register
from .dashboard_item import DashboardItem
# from .can_sender.canlib_metadata import CanlibMetadata
import sources.parsley.message_types as mt 

@Register
class CanSender(DashboardItem):
    """
    Visual blueprint of the CanSender dashboard item:
                  
    |-------------------------------------------------------------|
    | msg_type | board_id | time             | command |          | <- field names
    |----------|----------|------------------|---------|----------|
    | Dropdown | Dropdown | 24-bit Textfield | Dropdown|   Send   | <- field-dependent widgets to gather input
    |----------|-----------------------------|---------|----------|
    |   Port:  |   /dev/tty.usbmodem142201   |         |          | <- TODO: customize which port to send CAN message to
    |-------------------------------------------------------------|

    - Dropdowns contain a field's dictionary keys
        => when a Switch is encountered, populate the first key's fields
    - Text fields contain two different input masks:
        => Numerics: only hexadecimal values (TODO: I think user-input should be post-scaled but would need a way to communicate that)
        => ASCII: any string
    - Upon pressing send:
        => for every field that fails to encode its data, pulse the field in quick successions (comfy red)
        => if every field successfully encodes its data, long pulse all of the fields once (comfy green)
    - Width of CanSender widget scales depending on the CAN message length
    """

    def __init__(self):
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

        self.numeric_mask = "[A-Fa-f0-9]" # not sure if we want to stick with base 16 or base 10 (how to deal with scaled?)
        self.ascii_mask = "[\x00-\x7F]"

        self.timer = QTimer()
        self.timer.timeout.connect(self.pulse_invalid_fields)
        self.invalid_indexes = []

        # i dont want to constantly create/delete widgets from my arrays, so I'll use the idea
        # of an array-implemented stack where you 'delete' by moving your index pointer
        self.fields = [None] * 16
        self.widgets = [None] * 16
        self.widget_labels = [None] * 16
        self.widget_index = -1
        self.widget_to_index = {}

        self.add_fields([CAN_MSG])
        self.send_button = QPushButton("SEND")
        # self.send_button.clicked.connect(self.send_can_message)
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index + 1)

        # TODO: add the port thing here

        # constants
        self.NUM_PULSES = 3 # number of pulses to display when a Field throws an error
        self.PULSE_PERIOD = 100 # period (ms) between each pulse
        # self.MAX_MESSAGE_BYTES = 8

    def add_fields(self, fields: List[pf.Field]):
        for field in fields:
            self.widget_index += 1
            byte_length = field.length // 4
            match field:
                case pf.Switch, pf.Enum:
                    dropdown = QComboBox()
                    dropdown.setMinimumContentsLength(20) # TODO: I swear this changed the height of row entries but I mgiht be capping
                    dropdown_items = list(field.map_key_enum.keys())
                    dropdown.addItems(dropdown_items)
                    self.widgets[self.widget_index] = dropdown
                case pf.Numeric, pf.ASCII:
                    mask = self.numeric_mask if isinstance(field, pf.Numeric) else self.ascii_mask
                    textfield = QLineEdit()
                    textfield.setAlignment(Qt.AlignCenter)
                    textfield.setValidator(byte_length * mask)
                    textfield.setPlaceholderText(byte_length * "0")
                    textfield.installEventFilter(self) # intercept certain key press events for UX enchancements
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
            label = self.widget_label[index]
            self.layout_manager.remove(widget)
            self.layout_manager.remove(label)
            # need to delete widget from memory (i think it works like this or its deleteLater())
            widget = None
            label = None

        # insert the new widgets
        self.layout_manager.remove(self.send_button) # need to move the send button based on the length of the new can message
        self.widget_index = dropdown_index
        switch_field = self.fields[self.widget_index]
        nested_fields = switch_field.get_fields(text)
        self.add_fields(nested_fields)
        self.layout_manager.addWidget(self.send_button, 1, self.widget_index + 1)
        self.layout_manager.update()

    def send_can_message(self):
        # im not sure what the ideal way of this is, we can:
        # 1) check for valid fields, then parse fields (but thats a bit redudnant)
        # 2) data = parse fields, then do a match case check (if its None, then pulse errors) => but I want to collect all the errors to pulse at once instead of castcading
        bit_str = self.parse_can_msg()

        if bit_str == None:
            return
        # self.omnibus_sender.send(self.channel, self.parse_data())

    def parse_can_msg(self):
        self.invalid_indexes = []
        bit_str = BitString()
        for index in range(0, self.widget_index + 1):
            field = self.fields[index]
            text = self.widgets[index].text()
            try:
                bit_str.push(*field.encode(text))
            except:
                self.invalid_indexes.append(index)

        if self.invalid_indexes:
            self.pulse_count = 0
            self.timer.start(self.PULSE_PERIOD)

        return None if self.invalid_indexes else bit_str

    def pulse_invalid_fields(self):
        if self.pulse_count < self.NUM_PULSES*2:
            for index in self.invalid_indexes:
                widget = self.widgets[index]
                widget.setDisabled(self.pulse_count%2 == 0)
            self.pulse_count += 1
        else:
            self.timer.stop()

    def eventFilter(self, widget, event):
        """
        Intercept key press events from textfield to enhance UX.

        If backspace is pressed, we will try to move the cursor to the previous widget
        If shift + tab is pressed, we will move the cursor to the previous widget
        If tab is pressed, we will move the cursor to the next widget
        If any valid textfield characters are inputted, we will try to move the cursor to the next widget
        """
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(widget, event) # we don't need this event, let QLineEdit handle it
        match event.key():
            case Qt.Key_Backspace:
                self.try_move_cursor_backwards()
            case Qt.Key_Tab:
                match event.modifiers():
                    case Qt.ShiftModifier:
                        self.move_cursor_backwards()
                    case Qt.NoModifier:
                        self.move_cursor_forwards()
            case _:
                prev_text = widget.text()
                # let textfield handle the event and check if the character was added to the textfield
                # remember, we intercept messages, so we dont want to emit a move_cursor_fowards if the
                # message didn't even pass our input mask
                handled = super().eventFilter(widget, event)
                new_text = widget.text()
                self.capitalize_text()
                if prev_text != new_text:
                    self.try_move_cursor_forwards()
                return handled
        return super().eventFilter(widget, event) # we've finished intercepting the event, let QLineEdit handle the rest

    def capitalize_text(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
        field = self.fields[index]

        # keep numeric hexadecimals uppercase by default
        if isinstance(field, pf.Numeric):
            widget.setText(widget.text().upper())

    def try_move_cursor_forwards(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
        field = self.fields[index]
        byte_length = field.length // 4
        text_length = len(widget.text())

        if text_length == byte_length:
            self.move_cursor_forwards()

    def move_cursor_forwards(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
        next_index = min(self.widget_index, index + 1)
        next_widget = self.widgets[next_index]
        next_widget.setFocus()

    def try_move_cursor_backwards(self):
        widget = self.sender()
        text_length = len(widget.text())

        if text_length == 0:
            self.move_cursor_backwards()

    def move_cursor_backwards(self):
        widget = self.sender()
        index = self.widget_to_index[widget]
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

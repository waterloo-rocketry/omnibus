from typing import List
from pyqtgraph.Qt.QtCore import Qt
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
        # self.create_widgets()
        # self.setup_widgets()
        # self.place_widQCgets()

    def initialize_variables(self):
        self.layout_manager = QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.numeric_mask = "[A-Fa-f0-9]" # not sure if we want to stick with base 16 or base 10 (how to deal with scaled?)
        self.ascii_mask = "[[\x00-\x7F]]"

        self.fields = []
        self.fields_index = {}
        self.widgets = []
        self.widget_labels = []
        self.add_fields([CAN_MSG])

        # TODO: define common alignments (or make a function for them)
        # TODO: define text field input masks

        # constants
        self.NUM_PULSES = 3 # number of pulses to display when a Field throws an error
        self.PULSE_PERIOD = 100 # period (ms) between each pulse
        # self.MAX_MESSAGE_BYTES = 8

    def add_fields(self, fields: List[pf.Field]):
        for field in fields:
            index = len(self.fields) # index of the new parsley field to be added
            self.fields_index[index] = field # create mapping between parsley field and its index in the can message
            self.widget_labels.append(field.name) # label for the ith parsley field
            byte_legnth = field.length // 4
            match field:
                case pf.Switch, pf.Enum:
                    dropdown = QComboBox()
                    dropdown.setMinimumContentsLength(20) # TODO: I swear this changed the height of row entries but I mgiht be capping
                    dropdown_items = list(field.map_key_enum.keys())
                    dropdown.addItems(dropdown_items)

                    self.widgets.append(dropdown)
                    self.layout_manager.addWidget(self.widget_labels[index], 0, index) # TODO: create dynamic width based on can bit length
                    self.layout_manager.addWidget(self.widgets[index], 1, index) # TODO: create dynamic width based on can bit length

                    # I cant put the layout manager stuff at the end or else this recursive function ruins the order
                    if isinstance(field, pf.Switch):
                        nested_fields = field.get_fields(dropdown_items[0])
                        self.add_fields(nested_fields)
                case pf.Numeric:
                    textfield = QLineEdit()
                    textfield.setAlignment(Qt.AlignCenter)
                    textfield.setValidator(byte_legnth * self.numeric_mask)
                    # textfield.installEventFilter(BackspaceEventFilter())
                    textfield.setPlaceholderText(byte_legnth * "0")

                    self.widgets.append(textfield)
                    self.layout_manager.addWidget(self.widget_labels[index], 0, index)
                    self.layout_manager.addWidget(self.widgets[index], 1, index)
                case pf.ASCII:
                    textfield = QLineEdit() # mgiht be able to collapse this with Numeric (and just have a ternary for the validator)
                    textfield.setAlignment(Qt.AlignCenter)
                    textfield.setValidator(byte_legnth * self.ascii_mask)
                    textfield.setPlaceholderText(byte_legnth * "0")

                    self.widgets.append(textfield)
                    self.layout_manager.addWidget(self.widget_labels[index], 0, index)
                    self.layout_manager.addWidget(self.widgets[index], 1, index)

    def create_widgets(self):
        # CAN message type
        self.message_type = QComboBox()
        self.message_type.setPlaceholderText("Message Type")
        # self.message_type.addItems(self.canlib_info.get_msg_type())

        # CAN message data
        self.line_edits = []
        self.line_edits_map = {}
        for i in range(self.MAX_MESSAGE_BYTES):
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("00")
            line_edit.setAlignment(Qt.AlignCenter)
            # assign uuid to obtain line_edit <=> index relationship
            line_edit.setObjectName("QLineEdit #{}".format(i))
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i
        self.send = QPushButton("SEND", self)

        # 2d array of labels that remind users what datatype belongs to what column
        # self.labels[i][0] = top row, self.labels[i][1] = bototom row
        self.labels = []
        for i in range(self.MAX_MESSAGE_BYTES):
            top_label = QLabel()
            top_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
            top_label.setWordWrap(True)
            bot_label = QLabel()
            bot_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            bot_label.setWordWrap(True)
            self.labels.append([top_label, bot_label])
            self.labels[i][i%2].setText("None")

    def setup_widgets(self):
        # locks/unlocks input fields based on the updated msg_type
        self.message_type.currentTextChanged.connect(self.refresh_widget_info)
        # input mask for valid msg_data characters, blocks all other characters not in this regex
        valid_hexes = QRegularExpressionValidator("[A-Fa-f0-9][A-Fa-f0-9]")
        # customizing palette to ensure input fields have that "disabled" look
        self.palette = QPalette()
        self.palette.setColor(QPalette.Disabled, QPalette.Base, QColor("darkGrey"))
        # tracks when a backspace has been pressed for UX purposes
        self.backspace_event_filter = BackspaceEventFilter()
        self.backspace_event_filter.valid_backspace.connect(self.move_cursor_backwards)
        for i in range(self.MAX_MESSAGE_BYTES):
            self.line_edits[i].setValidator(valid_hexes)
            self.line_edits[i].setPalette(self.palette)
            self.line_edits[i].installEventFilter(self.backspace_event_filter)
            self.line_edits[i].textChanged.connect(self.move_cursor_forwards)
        self.send.clicked.connect(self.send_can_message)

    def place_widgets(self):
        # format: addWidget(row, col, height, width)
        self.layout_manager.addWidget(self.message_type, 1, 0, 1, 2)
        self.layout_manager.addWidget(self.send, 1, self.MAX_MESSAGE_BYTES+3, 1, 1)
        for i in range(self.MAX_MESSAGE_BYTES):
            self.layout_manager.addWidget(self.labels[i][0],  0, i+2, 1, 1)
            self.layout_manager.addWidget(self.line_edits[i], 1, i+2, 1, 1)
            self.layout_manager.addWidget(self.labels[i][1],  2, i+2, 1, 1)

#     def send_can_message(self):
#         if not self.has_invalid_fields():
#             self.omnibus_sender.send(self.channel, self.parse_data())
        
#     def parse_data(self):
#         msg_type = self.message_type.currentText()
#         msg_data = b""
# #        amt_of_data = len(self.canlib_info.get_msg_data(msg_type))
#         for i in range(amt_of_data):
#             # pad data with 0s until len = 2
#             # TODO: check if this is actually necessar, i dont think it is
#             msg_data += bytes.fromhex(self.line_edits[i].text().zfill(2))

#         msg_type = mt.msg_type_hex[msg_type]
#         msg_board = 0 # dummby board
#         msg_sid = msg_type | msg_board
        
#         formatted_data = {'message': (msg_sid, msg_data)}
#         return formatted_data

#     def has_invalid_fields(self):
#         bad_indexes = self.get_invalid_inputs()
#         if bad_indexes:
#             self.pulse_count = 0
#             self.timer = QTimer()
#             self.timer.timeout.connect(lambda: self.pulse(bad_indexes))
#             self.timer.start(self.PULSE_PERIOD)
#         return len(bad_indexes) > 0

#     def pulse(self, indexes):
#         if self.pulse_count < self.NUM_PULSES*2:
#             for i in indexes:
#                 widget = self.message_type if i == -1 else self.line_edits[i]
#                 widget.setDisabled(self.pulse_count%2 == 0)
#             self.pulse_count += 1
#         else:
#             self.timer.stop()

#     def get_invalid_inputs(self):
#         bad_indexes = []
#         msg_type = self.message_type.currentText()
#  #       msg_data_info = self.canlib_info.get_msg_data(msg_type)
#         if not msg_type:
#             bad_indexes.append(-1)
#         for i in range(len(msg_data_info)):
#             if not self.line_edits[i].text():
#                 bad_indexes.append(i)
#         return bad_indexes

#     def refresh_widget_info(self, new_msg_type):
#  #       msg_data = self.canlib_info.get_msg_data(new_msg_type)
#         amount_of_data = len(msg_data)
#         for i in range(self.MAX_MESSAGE_BYTES):
#             # locks input fields that aren't in use
#             self.line_edits[i].setEnabled(i < amount_of_data)
#             # resets labels/input boxes
#             self.labels[i][0].setText("")
#             self.labels[i][1].setText("")
#             # TODO: keep a temporray history of text so that if we go from 8 -> 4 back to 8 bytes,
#             # then the last 4 bytes of data is restored
#             self.line_edits[i].setText("")
#             self.line_edits[i].setPlaceholderText("")
#             if i < amount_of_data:
#                 # TODO: add astersik for label if mandatory
#                 self.labels[i][i%2].setText(msg_data[i])
#                 # TODO: add placeholder text if mandatory
#                 self.line_edits[i].setPlaceholderText("00")

#     def move_cursor_forwards(self):
#         obj = self.sender()
#         obj_name = obj.objectName()
#         cur_idx = self.line_edits_map[obj_name]
#         cur_len = len(self.line_edits[cur_idx].text())

#         obj.setText(obj.text().upper())
#         if cur_len == 2:
#             nxt_idx = min(self.MAX_MESSAGE_BYTES-1, cur_idx+1)
#             nxt_obj = self.line_edits[nxt_idx]
#             nxt_obj.setFocus()

#     def move_cursor_backwards(self):
#         obj_name = self.sender().objectName()
#         cur_idx = self.line_edits_map[obj_name]
#         cur_len = len(self.line_edits[cur_idx].text())

#         if cur_len == 0:
#             prv_idx = max(0, cur_idx-1)
#             prv_obj = self.line_edits[prv_idx]
#             prv_obj.setFocus()
#             prv_obj.setText(prv_obj.text()[:-1])

#     def get_name():
#         return "CAN Sender"

#     def get_props(self):
#         return True

#     def on_delete(self):
#         pass

#     def prompt_for_properties(self):
#         return True

# # there aren't any event handlers to check whether a certain key has been pressed
# # I need to know when a backspace has been pressed to potentially move the cursor back
# class BackspaceEventFilter(QObject):
#     valid_backspace = Signal()
#     __obj_name = ""

#     def eventFilter(self, obj, event):
#         if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Backspace:
#             self.__obj_name = obj.objectName()
#             self.valid_backspace.emit()
#         return super().eventFilter(obj, event)
    
#     def objectName(self):
#         return self.__obj_name

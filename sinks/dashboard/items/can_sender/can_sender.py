from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets
from omnibus import Sender
from parsers import publisher
from ..registry import Register
from ..dashboard_item import DashboardItem
from .canlib_metadata import CanlibMetadata
import sources.parsley.message_types as mt 

@Register
class CanSender(DashboardItem):
    """
    blueprint of grid layout
    |--------|----|----|----|----|------|
    | (0,0)  | lbl| lbl|... |lbl |(0,10)|
    |--------|----|----|----|----|------|
    |Msg Type|Byte|Byte|... |Byte|Button|
    |--------|----|----|----|----|------|
    | (2,0)  | lbl| lbl|... |lbl |(2,10)|
    |--------|----|----|----|----|------|
    Msg type = CAN bus message type
    Byte     = CAN bus data
    lbl      = describes the datatype in that column 
      => (only one of top or bottom label will be shown at a time)
    """
    NUM_PULSES = 3
    PULSE_FREQUENCY = 100 #in ms
    MAX_MESSAGE_BYTES = 8

    def __init__(self, props=None):
        super().__init__()

        self.layout_manager = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.canlib_info = CanlibMetadata("can_sender_data.txt")
        self.omnibus_sender = Sender()
        self.channel = "CAN/Commands"

        self.create_widgets()
        self.setup_widgets()
        self.place_widgets()

    def create_widgets(self):
        # CAN message type
        self.message_type = QtWidgets.QComboBox()
        self.message_type.setPlaceholderText("Message Type")
        self.message_type.addItems(self.canlib_info.get_msg_type())

        # CAN message data
        self.line_edits = []
        self.line_edits_map = {}
        for i in range(self.MAX_MESSAGE_BYTES):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setPlaceholderText("00")
            line_edit.setAlignment(QtCore.Qt.AlignCenter)
            # assign uuid to obtain line_edit <=> index relationship
            line_edit.setObjectName("QLineEdit #{}".format(i))
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i
        self.send = QtWidgets.QPushButton("SEND", self)

        # 2d array of labels that remind users what datatype belongs to what column
        # self.labels[i][0] = top row, self.labels[i][1] = bototom row
        self.labels = []
        for i in range(self.MAX_MESSAGE_BYTES):
            top_label = QtWidgets.QLabel()
            top_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
            top_label.setWordWrap(True)
            bot_label = QtWidgets.QLabel()
            bot_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            bot_label.setWordWrap(True)
            self.labels.append([top_label, bot_label])
            self.labels[i][i%2].setText("None")

    def setup_widgets(self):
        # locks/unlocks input fields based on the updated msg_type
        self.message_type.currentTextChanged.connect(self.refresh_widget_info)
        # input mask for valid msg_data characters, blocks all other characters not in this regex
        valid_hexes = QtGui.QRegularExpressionValidator("[A-Fa-f0-9][A-Fa-f0-9]")
        # customizing palette to ensure input fields have that "disabled" look
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor("darkGrey"))
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

    def send_can_message(self):
        if not self.has_invalid_fields():
            self.omnibus_sender.send(self.channel, self.parse_data())
        
    def parse_data(self):
        msg_type = self.message_type.currentText()
        msg_data = b""
        amt_of_data = len(self.canlib_info.get_msg_data(msg_type))
        for i in range(amt_of_data):
            # pad data with 0s until len = 2
            # TODO: check if this is actually necessar, i dont think it is
            msg_data += bytes.fromhex(self.line_edits[i].text().zfill(2))

        msg_type = mt.msg_type_hex[msg_type]
        msg_board = 0 # dummby board
        msg_sid = msg_type | msg_board
        
        formatted_data = {'message': (msg_sid, msg_data)}
        return formatted_data

    def has_invalid_fields(self):
        bad_indexes = self.get_invalid_inputs()
        if bad_indexes:
            self.pulse_count = 0
            self.timer = QtCore.QTimer()
            self.timer.timeout.connect(lambda: self.pulse(bad_indexes))
            self.timer.start(self.PULSE_FREQUENCY)
        return len(bad_indexes) > 0

    def pulse(self, indexes):
        if self.pulse_count < self.NUM_PULSES*2:
            for i in indexes:
                widget = self.message_type if i == -1 else self.line_edits[i]
                widget.setDisabled(self.pulse_count%2 == 0)
            self.pulse_count += 1
        else:
            self.timer.stop()

    def get_invalid_inputs(self):
        bad_indexes = []
        msg_type = self.message_type.currentText()
        msg_data_info = self.canlib_info.get_msg_data(msg_type)
        if not msg_type:
            bad_indexes.append(-1)
        for i in range(len(msg_data_info)):
            if not self.line_edits[i].text():
                bad_indexes.append(i)
        return bad_indexes

    def refresh_widget_info(self, new_msg_type):
        msg_data = self.canlib_info.get_msg_data(new_msg_type)
        amount_of_data = len(msg_data)
        for i in range(self.MAX_MESSAGE_BYTES):
            # locks input fields that aren't in use
            self.line_edits[i].setEnabled(i < amount_of_data)
            # resets labels/input boxes
            self.labels[i][0].setText("")
            self.labels[i][1].setText("")
            # TODO: keep a temporray history of text so that if we go from 8 -> 4 back to 8 bytes,
            # then the last 4 bytes of data is restored
            self.line_edits[i].setText("")
            self.line_edits[i].setPlaceholderText("")
            if i < amount_of_data:
                # TODO: add astersik for label if mandatory
                self.labels[i][i%2].setText(msg_data[i])
                # TODO: add placeholder text if mandatory
                self.line_edits[i].setPlaceholderText("00")

    def move_cursor_forwards(self):
        obj = self.sender()
        obj_name = obj.objectName()
        cur_idx = self.line_edits_map[obj_name]
        cur_len = len(self.line_edits[cur_idx].text())

        obj.setText(obj.text().upper())
        if cur_len == 2:
            nxt_idx = min(self.MAX_MESSAGE_BYTES-1, cur_idx+1)
            nxt_obj = self.line_edits[nxt_idx]
            nxt_obj.setFocus()

    def move_cursor_backwards(self):
        obj_name = self.sender().objectName()
        cur_idx = self.line_edits_map[obj_name]
        cur_len = len(self.line_edits[cur_idx].text())

        if cur_len == 0:
            prv_idx = max(0, cur_idx-1)
            prv_obj = self.line_edits[prv_idx]
            prv_obj.setFocus()
            prv_obj.setText(prv_obj.text()[:-1])

    def get_name():
        return "CAN Sender"

    def get_props(self):
        return True

    def on_delete(self):
        pass

    def prompt_for_properties(self):
        return True

# there aren't any event handlers to check whether a certain key has been pressed
# I need to know when a backspace has been pressed to potentially move the cursor back
class BackspaceEventFilter(QtCore.QObject):
    valid_backspace = QtCore.Signal()
    __obj_name = ""

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Backspace:
            self.__obj_name = obj.objectName()
            self.valid_backspace.emit()
        return super().eventFilter(obj, event)
    
    def objectName(self):
        return self.__obj_name

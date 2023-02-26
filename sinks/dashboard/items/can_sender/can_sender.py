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
    QGridLayout blueprint
    |--------|----|----|----|----|------|
    | (0,0)  | lbl| lbl|... |lbl |(0,10)|
    |--------|----|----|----|----|------|
    |Msg Type|Byte|Byte|... |Byte|Button|
    |--------|----|----|----|----|------|
    | (2,0)  | lbl| lbl|... |lbl |(2,10)|
    |--------|----|----|----|----|------|
    Msg type = CAN bus message type
    Byte     = CAN bus data
    lbl      = describes the type of data in that column
    """
    __pulse_occurances = 3
    __pulse_frequency = 100 #in ms
    __number_of_bytes = 8

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout_manager = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.canlib_info = CanlibMetadata("can_sender_data.txt")
        self.sender_thing = Sender()
        self.channel = "CAN/Commands"

        self.setupWidgets()
        self.logicfyWidgets()
        self.placeWidgets()

    def setupWidgets(self):
        # CAN bus message type
        self.message_type = QtWidgets.QComboBox()
        self.message_type.setPlaceholderText("Message Type")
        self.message_type.addItems(self.canlib_info.get_msg_type())

        # CAN bus message data
        self.line_edits = []
        self.line_edits_map = {}
        for i in range(self.__number_of_bytes):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setPlaceholderText("00")
            line_edit.setAlignment(QtCore.Qt.AlignCenter)
            # assign uuid to obtain line_edit <=> index relationship
            line_edit.setObjectName("QLineEdit #{}".format(i))
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i
        self.send = QtWidgets.QPushButton("SEND", self)

        # 2d array of QLabels that dictate what kind of datatype belonds to this column
        # self.labels[i][0] = top, self.labels[i][1] = bot labels
        self.labels = []
        for i in range(self.__number_of_bytes):
            top_label = QtWidgets.QLabel()
            top_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
            top_label.setWordWrap(True)
            bot_label = QtWidgets.QLabel()
            bot_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            bot_label.setWordWrap(True)
            self.labels.append([top_label, bot_label])
            self.labels[i][i%2].setText("None")

    def logicfyWidgets(self):
        # locks/unlocks QLineEdits based on the updated msg_type
        self.message_type.currentTextChanged.connect(self.refresh_widget_info)
        # input mask for valid msg_data characters
        valid_hexes = QtGui.QRegularExpressionValidator("[A-Fa-f0-9][A-Fa-f0-9]")
        # customizing palette to ensure QLineEdits have that "disabled" look
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor("darkGrey"))
        # tracks when a backspace has been pressed
        self.backspace_event_filter = BackspaceEventFilter()
        self.backspace_event_filter.valid_backspace.connect(self.move_cursor_backwards)
        for i in range(self.__number_of_bytes):
            self.line_edits[i].setValidator(valid_hexes)
            self.line_edits[i].setPalette(self.palette)
            self.line_edits[i].installEventFilter(self.backspace_event_filter)
            self.line_edits[i].textChanged.connect(self.move_cursor_forwards)
        self.send.clicked.connect(self.send_can_message)

    def placeWidgets(self):
        # format: addWidget(row, col, height, width)
        self.layout_manager.addWidget(self.message_type, 1, 0, 1, 2)
        self.layout_manager.addWidget(self.send, 1, self.__number_of_bytes+3, 1, 1)
        for i in range(self.__number_of_bytes):
            self.layout_manager.addWidget(self.labels[i][0],  0, i+2, 1, 1)
            self.layout_manager.addWidget(self.line_edits[i], 1, i+2, 1, 1)
            self.layout_manager.addWidget(self.labels[i][1],  2, i+2, 1, 1)

    def send_can_message(self):
        # there were invalid field(s) and we pulsed, dont send message
        if self.pulse_widgets():
            return
        self.sender_thing.send(self.channel, self.parse_data())
        
    def parse_data(self):
        msg_type = self.message_type.currentText()
        msg_data = b""
        amt_of_data = len(self.canlib_info.get_msg_data(msg_type))
        for i in range(amt_of_data):
            # padding text with 0 until len = 2
            msg_data += bytes.fromhex(self.line_edits[i].text().zfill(2))

        msg_type = mt.msg_type_hex[msg_type]
        msg_board = 0
        msg_sid = msg_type | msg_board
        
        """
         dont hate the player hate the game tldr omnibus dashboard receives all messages
         being sent and requires that there be a [data][time] in the message object so...
        """
        formatted_data = {'data': {'time': -1}, 'message': (msg_sid, msg_data)}
        return formatted_data

    def pulse_widgets(self):
        bad_indexes = self.get_invalid_bytes()
        self.pulse_count = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(lambda: self.pulse(bad_indexes))
        self.timer.start(self.__pulse_frequency)
        return len(bad_indexes) > 0 # return whether we pulsed (error) anything

    def pulse(self, indexes):
        if self.pulse_count < self.__pulse_occurances*2:
            for i in indexes:
                widget = self.message_type if i == -1 else self.line_edits[i]
                widget.setDisabled(self.pulse_count%2 == 0)
            self.pulse_count += 1
        else:
            self.timer.stop()

    def get_invalid_bytes(self):
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
        for i in range(self.__number_of_bytes):
            # locks that data bytes that aren't in use
            self.line_edits[i].setEnabled(i < amount_of_data)
            # clears and sets the new msg_data datatype
            self.labels[i][0].setText("")
            self.labels[i][1].setText("")
            if i < amount_of_data:
                self.labels[i][i%2].setText(msg_data[i])

    def move_cursor_forwards(self):
        obj = self.sender()
        obj.setText(obj.text().upper())
        obj_name = obj.objectName()
        cur_idx = self.line_edits_map[obj_name]
        cur_len = len(self.line_edits[cur_idx].text())

        if cur_len == 2:
            nxt_idx = min(self.__number_of_bytes-1, cur_idx+1)
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
        return self.props

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

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

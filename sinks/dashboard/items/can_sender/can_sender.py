from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets
from ..dashboard_item import DashboardItem
from parsers import publisher
from ..registry import Register
import sources.parsley.message_types as mt
from omnibus import Sender
from .canlib_metadata import CanlibMetadata

# not sure if this should be a nested class
class BackspaceEventFilter(QtCore.QObject):
    valid_backspace = QtCore.Signal()
    name = "n/a"

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Backspace and len(obj.text())==0:
            self.name = obj.objectName()
            self.valid_backspace.emit()
        return super().eventFilter(obj, event)

@Register
class CanMsgSndr(DashboardItem):
    """
    Display table for CAN messages.
|--------|----|----|----|----|------|
| (0,0)  | lbl| lbl|... |lbl |(0,10)|
|--------|----|----|----|----|------|
|Msg Type|Byte|Byte|... |Byte|Button|
|--------|----|----|----|----|------|
| (2,0)  |    |    |    |    |(2,10)|
|--------|----|----|----|----|------|
    Using the QGridLayout to structure the layout
    Msg type = the type of message to send
    Byte     = the 2 hexadecimal message
    lbl      = the "datatype" occupied at that column
    """

    def onDataChange(self):
        obj_name = self.sender().objectName()
        cur_idx = self.line_edits_map[obj_name]
        cur_len = len(self.line_edits[cur_idx].text())

        if cur_len == 2:
            nxt_idx = min(7, cur_idx+1)
            nxt_obj = self.line_edits[nxt_idx]
            nxt_obj.setFocus()

    def onMessageTypeChange(self, newMsgType):
        # unlocks the amount of bytes based on canlib, locks the rest
        byteInfo = self.canlib_info.getDataInfo(newMsgType)
        amountOfUnlocks = len(byteInfo)
        for i in range(len(self.line_edits)):
            self.line_edits[i].setReadOnly(i >= amountOfUnlocks)
            self.line_edits[i].setDisabled(i >= amountOfUnlocks)
            self.labels[i][0].setText("")
            self.labels[i][1].setText("")
            if i < amountOfUnlocks:
                # alternating between top and bottom label
                self.labels[i][i%2].setText(byteInfo[i])

    def onBackspace(self):
        obj_name = self.sender().name # TODO: this is so hacky
        cur_idx = self.line_edits_map[obj_name]
        prv_idx = max(0, cur_idx-1)
        prv_obj = self.line_edits[prv_idx]
        prv_obj.setFocus()
        prv_obj.setText(prv_obj.text()[:-1])

    def onButtonPress(self):
        msg_type = self.message_type.currentText()
        msg_data = b""
        byteInfo = self.canlib_info.getDataInfo(msg_type)
        if not msg_type: # QComboText has placeholder text
            return
        for i in range(len(byteInfo)):
            if not self.line_edits[i]: # QLineEdit is empty
                return
            # padding text with 0 until len = 2
            msg_data += bytes.fromhex(self.line_edits[i].text().zfill(2))

        msg_type = mt.msg_type_hex[msg_type]
        msg_board = 0 # QUESTION: do we have a special omnibus board id?
        msg_sid = msg_type | msg_board
        
        """
         dont hate the player hate the game tldr omnibus dashboard receives all messages
         and requires that there be a [data][time] in the messages so...
        """
        formatted_data = {'data': {'time': -1}, 'message': (msg_sid, msg_data)}
        print(formatted_data)
        self.sender_thing.send(self.channel, formatted_data)

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout_manager = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.canlib_info = CanlibMetadata("can_sender_data.txt")

        self.setupWidgets()
        self.logicfyWidgets()
        self.placeWidgets()

        self.sender_thing = Sender() #this name collashes with something else, need better name
        self.channel = "CAN/Commands"
        
    def getValidMessageTypes(self):
        return self.canlib_info.getMessageTypes()


    def setupWidgets(self):
        # CAN bus message type
        self.message_type = QtWidgets.QComboBox()
        self.message_type.setPlaceholderText("Message Type")
        self.message_type.addItems(self.getValidMessageTypes())

        # CAN bus message data
        self.line_edits = []
        self.line_edits_map = {}
        for i in range(8):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setPlaceholderText("00")
            line_edit.setAlignment(QtCore.Qt.AlignCenter)
            # assign uuid to obtain line_edit <=> index relationship
            line_edit.setObjectName("QLineEdit #{}".format(i))
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i

        self.send = QtWidgets.QPushButton("SEND", self)

        # array of QLabels that dictate what kind of datatype belonds to this column
        self.labels = [] #2d array of labels, 0 = top, 1 = bot labels
        for i in range(8):
            top_label = QtWidgets.QLabel("None")
            top_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
            top_label.setWordWrap(True)

            bot_label = QtWidgets.QLabel()
            bot_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            bot_label.setWordWrap(True)
            self.labels.append([top_label, bot_label])

    def logicfyWidgets(self):
        # locks/unlocks QLineEdits based on the msg type that was changed
        self.message_type.currentTextChanged.connect(self.onMessageTypeChange)

        # qol additions for message_data
        valid_hexes = QtGui.QRegularExpressionValidator("[A-F0-9][A-F0-9]")
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor("darkGrey"))
        self.backspace_event_filter = BackspaceEventFilter()
        self.backspace_event_filter.valid_backspace.connect(self.onBackspace)
        for i in range(len(self.line_edits)):
            # applying regex input mask
            self.line_edits[i].setValidator(valid_hexes)
            # ensuring QLineEdits "look" disabled
            self.line_edits[i].setPalette(self.palette)
            # emits that a backspace was pressed (not possible through default api afaik)
            self.line_edits[i].installEventFilter(self.backspace_event_filter)
            # if current data byte is full, mouse becomes focused onto next data byte 
            self.line_edits[i].textChanged.connect(self.onDataChange)

        # on button press, try to send message to parsley
        self.send.clicked.connect(self.onButtonPress)

    def placeWidgets(self):
        self.layout_manager.addWidget(self.message_type, 1, 0, 1, 1)

        for i in range(len(self.line_edits)):
            self.layout_manager.addWidget(self.line_edits[i], 1, i+2, 1, 1)

        self.layout_manager.addWidget(self.send, 1, 11, 1, 1)

        for i in range(len(self.labels)):
            self.layout_manager.addWidget(self.labels[i][0], 0, i+2, 1, 1)
            self.layout_manager.addWidget(self.labels[i][1], 2, i+2, 1, 1)

    def get_name():
        return "CAN Sender"

    def get_props(self):
        return self.props

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

    def prompt_for_properties(self):
        return True

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

    def onMessageTypeChange(self):
        obj = self.sender()

        if obj is None or obj.text() not in self.getValidMessageTypes():
            self.lockLineEdit(0) 
        else: 
            amt_of_unlock = 0 if obj.text() in ["LEDS_ON", "LEDS_OFF"] else 8 # TODO 
            self.lockLineEdit(amt_of_unlock)

    # 0-indexed
    def lockLineEdit(self, amountOfUnlocks):
        for i in range(len(self.line_edits)):
            self.line_edits[i].setReadOnly(i >= amountOfUnlocks)
            self.line_edits[i].setDisabled(i >= amountOfUnlocks)

    def onBackspace(self):
        obj_name = self.sender().name # TODO: this is so hacky
        cur_idx = self.line_edits_map[obj_name]
        prv_idx = max(0, cur_idx-1)
        prv_obj = self.line_edits[prv_idx]
        prv_obj.setFocus()
        prv_obj.setText(prv_obj.text()[:-1])

    def onButtonPress(self):
        if not self.message_type.text() in self.getValidMessageTypes():
            return
        # check valid message type 
        # check that unlocked bytes are filled
        # check that unlocked bytes are valid

        msg_type = mt.msg_type_hex[self.message_type.text()]
        msg_board = 0 # QUESTION: do we have a special omnibus board id?
        msg_sid = msg_type | msg_board
        msg_data = "".join(byte.text() for byte in self.line_edits)
        
        """
         dont hate the player hate the game tldr omnibus dashboard receives all messages
         and requires that there be a [data][time] in the messages so...
        """
        formatted_data = {'data': {'time': -1}, 'message': (msg_sid, msg_data)}
        self.sender_thing.send(self.channel, formatted_data)

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout_manager = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.canlib_info = CanlibMetadata("can_sender_data.txt")
        print(self.canlib_info.getMessageTypes())

        self.setupWidgets()
        self.logicfyWidgets()
        self.placeWidgets()

        self.sender_thing = Sender() #this name collashes with something else, need better name
        self.channel = "CAN/Commands"
        
    def getValidMessageTypes(self):
        return self.canlib_info.getMessageTypes()


    def setupWidgets(self):
        # CAN bus message type
        # self.message_type = QtWidgets.QLineEdit(self)
        # self.message_type.setPlaceholderText("Message Type")

        self.message_type = QtWidgets.QComboBox()
        for msg_type in self.getValidMessageTypes():
            self.message_type.addItem(msg_type)
        # self.message_type.addItem(self.getValidMessageTypes())

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
        self.top_labels = []
        self.bot_labels = []
        for i in range(8):
            top_label = QtWidgets.QLabel("None")
            # top_label.setStyleSheet("border: 1px solid black;")
            top_label.setAlignment(QtCore.Qt.AlignBottom | QtCore.Qt.AlignLeft)
            top_label.setWordWrap(True)
            self.top_labels.append(top_label)

            bot_label = QtWidgets.QLabel()
            # bot_label.setStyleSheet("border: 1px solid black;")
            bot_label.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
            bot_label.setWordWrap(True)
            self.bot_labels.append(bot_label)

    def logicfyWidgets(self):
        # applying auto complete list onto message_type
        # auto_complete = QtWidgets.QCompleter(self.getValidMessageTypes(), self)
        # self.message_type.setCompleter(auto_complete)
        # self.message_type.textChanged.connect(self.onMessageTypeChange)
        # self.onMessageTypeChange() # apply so they start disabled

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

        for i in range(len(self.top_labels)):
            self.layout_manager.addWidget(self.top_labels[i], 0, i+2, 1, 1)
            self.layout_manager.addWidget(self.bot_labels[i], 2, i+2, 1, 1)

    def get_name():
        return "CAN Sender"

    def get_props(self):
        return self.props

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

    def prompt_for_properties(self):
        return True

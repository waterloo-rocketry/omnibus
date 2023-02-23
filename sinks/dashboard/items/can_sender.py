from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtWidgets
from .dashboard_item import DashboardItem
from parsers import publisher
from .registry import Register

# So, we need a few things
# 1) a widget that displays an object, in our case a
#    CAN Message. Will be a QTable
# 2) An expandable and collapsable widget which
#    will allow us to filter the table as we wish
# 3) A large container, which we will use to update
#    the object display with messages


class LayoutWidget(QtWidgets.QWidget):
    """
    A widget whose sole job is to hold
    a layout. The hacky stuff QT makes 
    me do smh.
    """

    def __init__(self, layout):
        super().__init__()
        self.layout = layout
        self.setLayout(self.layout)


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
    |    |    |    |    |    |
----|----|----|----|----|----|----
 0,0|    | lbl| lbl|... |lbl |0,11
----|----|----|----|----|----|----
 Msg type|Byte|Byte|... |Byte| Button
----|----|----|----|----|----|----
 2,0|    |    |    |    |    |2,11
----|----|----|----|----|----|----
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
            amt_of_unlock = 0 if obj.text() in ["LEDS_ON", "LEDS_OFF"] else 8
            print(amt_of_unlock)
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

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout_manager = QtWidgets.QGridLayout(self)
        self.setLayout(self.layout_manager)

        self.setupWidgets()
        self.placeWidgets()
        
        # Subscribe to all relavent stream
        publisher.subscribe("CAN/Commands", self.on_data_update)


    def prompt_for_properties(self):
        return True

    def get_props(self):
        return self.props

    def on_data_update(self, stream, canSeries):
        message = canSeries[1]
        if message["board_id"] in self.message_dict:
            self.message_dict[message["board_id"]].update_with_message(message)
        else:
            table = DisplayCANTable()
            self.message_dict[message["board_id"]] = table
            exp_widget = ExpandingWidget(message["board_id"], table)
            self.layout_widget.layout.addWidget(exp_widget)
            self.message_dict[message["board_id"]].update_with_message(message)


    def get_name():
        return "CAN Sender"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

    def getValidMessageTypes(self):
        # this'll eventually be a map datastructure.map(get_name) or smth trust it'll be clean
        ret = ["LEDS_ON", "LEDS_OFF", "SENSOR_MAG"]
        return ret


    def setupWidgets(self):
        # message type with autocomplete to choose from
        auto_complete = QtWidgets.QCompleter(self.getValidMessageTypes(), self)
        self.message_type = QtWidgets.QLineEdit(self)
        self.message_type.setPlaceholderText("Message Type")
        self.message_type.setCompleter(auto_complete)
        self.message_type.textChanged.connect(self.onMessageTypeChange)

        # setting the color to look disabled
        self.palette = QtGui.QPalette()
        self.palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Base, QtGui.QColor("darkGrey"))

        # array of QLineEdits to represent data bytes
        valid_hexes = QtGui.QRegularExpressionValidator("[A-F0-9][A-F0-9]")
        self.line_edits = []
        self.line_edits_map = {}
        self.backspace_event_filter = BackspaceEventFilter()
        self.backspace_event_filter.valid_backspace.connect(self.onBackspace)
        for i in range(8):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setValidator(valid_hexes)
            line_edit.setPlaceholderText("00")
            line_edit.setAlignment(QtCore.Qt.AlignCenter)
            line_edit.setObjectName("QLineEdit #{}".format(i))
            line_edit.setPalette(self.palette)
            line_edit.installEventFilter(self.backspace_event_filter)
            line_edit.textChanged.connect(self.onDataChange)
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i

        self.send = QtWidgets.QPushButton(self)
        self.send.setText("SEND")

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

        # visual touches
        self.onMessageTypeChange()

    def placeWidgets(self):
        self.layout_manager.addWidget(self.message_type, 1, 0, 1, 1)

        for i in range(len(self.line_edits)):
            self.layout_manager.addWidget(self.line_edits[i], 1, i+2, 1, 1)

        self.layout_manager.addWidget(self.send, 1, 11, 1, 1)

        for i in range(len(self.top_labels)):
            self.layout_manager.addWidget(self.top_labels[i], 0, i+2, 1, 1)
            self.layout_manager.addWidget(self.bot_labels[i], 2, i+2, 1, 1)
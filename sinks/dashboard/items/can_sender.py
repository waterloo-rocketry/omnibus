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


class DisplayCANTable(QtWidgets.QWidget):
    """
    A widget that displays an object, in our case a
    CAN message. Makes use of a QTable.
    """

    def __init__(self):
        # Super Class Init
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.tableWidget = QtWidgets.QTableWidget()
        self.msgTypes = []
        self.msgInd = 0

        # 8 bytes, 3 used by time stamp leaves 6 total fields
        # + 1 title field
        self.tableWidget.setRowCount(7)

        height = self.tableWidget.horizontalHeader().height() + 25
        for i in range(self.tableWidget.rowCount()):
            height += self.tableWidget.rowHeight(i)

        self.tableWidget.setMinimumHeight(height)

        self.layout.addWidget(self.tableWidget)

    def update_with_message(self, msg):
        msg_type = msg["msg_type"]
        msg_data = msg["data"]
        # current hacky fix to ensure that SENSOR_ANALOG data isn't overwritten since different sensor Ids are sent at different times
        combo_type = f"{msg_type}_{msg_data['sensor_id']}" if msg_type == "SENSOR_ANALOG" else msg_type

        if combo_type not in self.msgTypes:
            self.msgTypes.append(combo_type)
            item = QtWidgets.QTableWidgetItem(combo_type)
            # taking advantage of this
            # https://www.riverbankcomputing.com/static/Docs/PyQt4/qt.html#AlignmentFlag-enum
            # because I had issues importing Qt.AlignHCenter
            item.setTextAlignment(4)

            # resize column
            self.tableWidget.setColumnCount(2 * len(self.msgTypes))
            for i in range(len(self.msgTypes)):
                self.tableWidget.setSpan(0, 2*i, 1, 2)

            font = QtGui.QFont()
            font.setBold(True)

            item.setFont(font)
            self.tableWidget.setItem(0, 2*self.msgInd, item)
            self.msgInd += 1

        index = -1

        for i in range(len(self.msgTypes)):
            if combo_type == self.msgTypes[i]:
                index = i

        for i, (k, v) in enumerate(msg_data.items()):
            key_item = QtWidgets.QTableWidgetItem(str(k))
            key_item.setTextAlignment(4)
            self.tableWidget.setItem(i+1, 2*index, key_item)

            value_item = QtWidgets.QTableWidgetItem(str(v))
            value_item.setTextAlignment(4)
            self.tableWidget.setItem(i+1, 2*index + 1, value_item)



    def toggle(self):
        if self.is_expanded:
            self.layout.removeWidget(self.content)
            self.content.setParent(None)
            self.expand_contract_action.setText(f"> {self.name}")
            self.is_expanded = False
        else:
            self.layout.addWidget(self.content)
            self.expand_contract_action.setText(f"V {self.name}")
            self.is_expanded = True


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
    """

    def onTextChange(self, new_text):
        obj_name = self.sender().objectName()
        cur_idx = self.line_edits_map[obj_name]
        cur_len = len(self.line_edits[cur_idx].text())

        if cur_len == 2:
            nxt_idx = min(7, cur_idx+1)
            nxt_obj = self.line_edits[nxt_idx]
            nxt_obj.setFocus()

    def onBackspace(self):
        obj_name = self.sender().name # this is so hacky
        cur_idx = self.line_edits_map[obj_name]
        prv_idx = max(0, cur_idx-1)
        prv_obj = self.line_edits[prv_idx]
        prv_obj.setFocus()

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout = QtWidgets.QHBoxLayout(self)
        self.setLayout(self.layout)

        self.layout_widget = LayoutWidget(QtWidgets.QHBoxLayout())

        self.msg_typ_part = QtWidgets.QLineEdit(self)
        self.msg_typ_part.setPlaceholderText("Message Type")


        valid_hexes = QtGui.QRegularExpressionValidator("[A-F0-9][A-F0-9]")
        self.line_edits = []
        self.line_edits_map = {}
        self.backspace_event_filter = BackspaceEventFilter()
        self.backspace_event_filter.valid_backspace.connect(self.onBackspace)
        for i in range(8):
            line_edit = QtWidgets.QLineEdit()
            line_edit.setValidator(valid_hexes)
            line_edit.setPlaceholderText("00")
            line_edit.setObjectName("QLineEdit #{}".format(i))
            line_edit.installEventFilter(self.backspace_event_filter)
            line_edit.textChanged.connect(self.onTextChange)
            self.line_edits.append(line_edit)
            self.line_edits_map[line_edit.objectName()] = i

        self.send = QtWidgets.QPushButton(self)
        self.send.setText("SEND")
        # Subscribe to all relavent stream
        publisher.subscribe("CAN/Commands", self.on_data_update)

        self.layout.addWidget(self.msg_typ_part, 2)
        for i in range(len(self.line_edits)):
            self.layout.addWidget(self.line_edits[i], 1)
        # self.layout.addWidget(self.input_part, 3)
        self.layout.addWidget(self.send)

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

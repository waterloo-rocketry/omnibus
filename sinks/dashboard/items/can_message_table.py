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


class ExpandingWidget(QtWidgets.QWidget):
    """
    A widget whose sole function is to contain a
    grid layout and expand and collapse on click
    """

    def __init__(self, name, widget):
        super().__init__()
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.name = name

        menubar = QtWidgets.QMenuBar(self)
        self.layout.setMenuBar(menubar)

        self.content = widget
        self.is_expanded = False

        self.expand_contract_action = menubar.addAction(f"> {self.name}")
        self.expand_contract_action.triggered.connect(self.toggle)

        # self.toggle()

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


@Register
class CanMsgTableDashItem(DashboardItem):
    """
    Display table for CAN messages.
    """

    def __init__(self, params=None):
        super().__init__(params)
        # 1) Establish a structure of one expanding
        #    widget per board
        # 2) For each of those widgets, add a Display
        #    object for each message type
        # 3) set the update function up in such a
        #    way that when a message is recieved, it
        #    is rendered in the right object

        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

        self.layout_widget = LayoutWidget(QtWidgets.QVBoxLayout())
        # self.layout_widget.resize(self.size().width(),1000)

        # lab = QtWidgets.QLabel()
        # img = QtGui.QImage("test.jpg")
        # lab.setPixmap(QtGui.QPixmap.fromImage(img))
        # self.layout_widget.layout.addWidget(lab)

        self.message_dict = {}
        # Each key is  board ID
        # Each value is another dictionary
        # within the second dictionary, each
        # key is a message type and the value is the
        # specific DisplayObject

        # Subscribe to all relavent stream
        publisher.subscribe("CAN", self.on_data_update)

        self.scrolling_part = QtWidgets.QScrollArea(self)
        self.scrolling_part.setWidgetResizable(True)
        self.scrolling_part.setWidget(self.layout_widget)

        self.layout.addWidget(self.scrolling_part)

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

    @staticmethod
    def get_name():
        return "CAN Message Table"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

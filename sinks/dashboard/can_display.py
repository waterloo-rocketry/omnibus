import collections as col

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from dashboarditem import DashboardItem
from sources.parsley.parsley import fmt_line
import sources.parsley.message_types as mt
from parsers import CanDisplayParser, BOARD_NAME_LIST

# --------------CONSTANTS---------------
HEALTHY_STATE_COLOR = "green"
UNHEALTHY_STATE_COLOR = "red"
MAX_MSG_QUEUE_SIZE = 50
HEALTHY_STATE_TIMEOUT = 10000  # 10s

# TODO: set better color schemes (AKA determine which colors are better for viewing)
BOARD_DATA = {"INJECTOR": {"id": 0x01, "index": 0, "color": QtGui.QColor('cyan')},
              "LOGGER": {"id": 0x03, "index": 1, "color": QtGui.QColor('darkCyan')},
              "RADIO": {"id": 0x05, "index": 2, "color": QtGui.QColor('blue')},
              "SENSOR": {"id": 0x07, "index": 3, "color": QtGui.QColor('darkblue')},
              "VENT": {"id": 0x0B, "index": 4, "color": QtGui.QColor('magenta')},
              "GPS": {"id": 0x0D, "index": 5, "color": QtGui.QColor('darkMagenta')},
              "ARMING": {"id": 0x11, "index": 6, "color": QtGui.QColor('green')},
              "PAPA": {"id": 0x13, "index": 7, "color": QtGui.QColor('darkGreen')},
              "ROCKET_PI": {"id": 0x15, "index": 8, "color": QtGui.QColor('pink')},
              "ROCKET_PI_2": {"id": 0x16, "index": 9, "color": QtGui.QColor('deeppink')},
              "SENSOR_2": {"id": 0x19, "index": 10, "color": QtGui.QColor('orange')},
              "SENSOR_3": {"id": 0x1B, "index": 11, "color": QtGui.QColor('darkorange')}}
CAN_HEALTH_STATES = ["DEAD"] * len(BOARD_DATA)
CAN_HEALTH_STATES_COLORS = [UNHEALTHY_STATE_COLOR] * len(BOARD_DATA)


class CanDisplayDashItem (DashboardItem):
    """
    Display for CAN messages.
    """

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.layout = QtWidgets.QGridLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)

        self.textBrowsers = {}
        self.browsersNextRow = 0

        self.pushButtonList = list(BOARD_DATA.keys())
        self.labels = []
        self.canNodes = {}

        self.rightGrid = QtWidgets.QVBoxLayout()

        for index, value in enumerate(list(BOARD_DATA.keys())):
            self.canNodes[index] = CanNodeWidgetDashItem(value)
            self.pushButtonList[index] = QtWidgets.QPushButton(value)
            self.pushButtonList[index].setCheckable(True)
            self.labels.append(QtWidgets.QLabel())
            # TODO: improve alignment
            self.rightGrid.addWidget(self.pushButtonList[index], index, QtCore.Qt.AlignCenter)
            self.rightGrid.addWidget(self.labels[index], index, QtCore.Qt.AlignCenter)
        self.layout.addLayout(self.rightGrid, 0, 1)
        self.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.groupbox

    def update_board_health_state(self):
        for node_name, node in self.canNodes.items():
            CAN_HEALTH_STATES[BOARD_DATA[node.board_id]["index"]] = node.board_status
            CAN_HEALTH_STATES_COLORS[BOARD_DATA[node.board_id]["index"]] = node.status_color

    def add_node_widget(self, widget_name):
        self.canNodes[BOARD_DATA[widget_name]["index"]].enable_widget()
        self.textBrowsers[widget_name] = {}
        self.textBrowsers[widget_name]["widget"] = self.canNodes[BOARD_DATA[widget_name]["index"]]
        self.layout.addWidget(
            self.textBrowsers[widget_name]["widget"].get_widget(), self.browsersNextRow, 0)
        self.browsersNextRow += 1

    def delete_node_widget(self, widget_name):
        self.layout.removeWidget(self.textBrowsers[widget_name]["widget"].get_widget())
        self.textBrowsers[widget_name]["widget"].disable_widget()
        del self.textBrowsers[widget_name]
        self.browsersNextRow = len(self.textBrowsers)

    def update(self):
        self.update_board_health_state()
        for index, value in enumerate(self.pushButtonList):
            self.labels[index].setStyleSheet(
                f"color : {CAN_HEALTH_STATES_COLORS[index]};")
            self.labels[index].setText(CAN_HEALTH_STATES[index])

            node_name = BOARD_NAME_LIST[index]
            if value.isChecked() and node_name not in self.textBrowsers.keys():
                self.add_node_widget(node_name)
            elif not value.isChecked() and node_name in self.textBrowsers.keys():
                self.delete_node_widget(node_name)


class CanNodeWidgetDashItem(DashboardItem):
    """
    Display for CAN messages.
    """

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        if self.props is None:
            # request board_id?
            self.board_id = "DUMMY"
        else:
            self.board_id = self.props
        self.board_index = BOARD_DATA[self.board_id]['index']
        self.oldCanMsgTime = 0
        self.currCanMsgTime = 0
        self.msgHistoryQ = col.deque(maxlen=MAX_MSG_QUEUE_SIZE)

        # Start in dead status until we receive a message from this board
        self.board_status = "DEAD"
        self.status_color = UNHEALTHY_STATE_COLOR

        self.textBrowser = None

        self.series = CanDisplayParser.get_canSeries(self.board_id)
        self.subscribe_to_series(self.series)

    def enable_widget(self):
        self.textBrowser = QtWidgets.QTextBrowser()

    def disable_widget(self):
        self.textBrowser.clear()
        self.textBrowser.deleteLater()
        self.textBrowser = None

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.textBrowser

    def updateHealthChecks(self):
        # Check our last health check for this index was over 10s ago, now in DEAD state
        if self.currCanMsgTime < abs(self.oldCanMsgTime - HEALTHY_STATE_TIMEOUT):
            CAN_HEALTH_STATES[self.board_index] = "DEAD_FROM_TIMEOUT"
            CAN_HEALTH_STATES_COLORS[self.board_index] = UNHEALTHY_STATE_COLOR
        else:
            self.oldCanMsgTime = self.currCanMsgTime

    def updateCanMsgTimes(self, msg):
        self.currCanMsgTime = msg["data"]["time"]

    # Note: this function definitely doesn't have the most efficient solutions but prevents memory issues
    def on_data_update(self, series):
        # get the newest msg
        newest_msg = series.get_msg()
        # update some internal trackers
        self.updateCanMsgTimes(newest_msg)
        self.updateHealthChecks()
        # check if our queue is already full, if so take off oldest msg
        if len(self.msgHistoryQ) == MAX_MSG_QUEUE_SIZE:
            self.msgHistoryQ.popleft()  # don't care about old message
        # put newest msg in queue
        self.msgHistoryQ.append(get_formatted_msg(newest_msg) + "\n")
        # update status
        if newest_msg["msg_type"] == "GENERAL_BOARD_STATUS":
            self.board_status = newest_msg["data"]["status"]
            self.status_color = get_status_color(self.board_status)

        # update textBrowser
        if self.textBrowser is not None:
            # clear old text before pushing updated history
            self.textBrowser.clear()
            self.textBrowser.setTextColor(BOARD_DATA[self.board_id]['color'])
            self.textBrowser.append("".join(str(ele) for ele in self.msgHistoryQ))

            # if scroll bar within 10 pixels of bottom, auto scroll to bottom
            scrollIsAtEnd = self.textBrowser.verticalScrollBar().maximum(
            ) - self.textBrowser.verticalScrollBar().value() <= 10
            if scrollIsAtEnd:
                self.textBrowser.verticalScrollBar().setValue(
                    self.textBrowser.verticalScrollBar().maximum())  # Scrolls to the bottom


# -----------------Helpers----------------
def get_status_color(status):
    if status in ["E_NOMINAL", "RECEIVED_MSG_NO_STATUS"]:
        return HEALTHY_STATE_COLOR
    else:
        return UNHEALTHY_STATE_COLOR


def get_formatted_msg(msg):
    formatted_msg = fmt_line(msg)
    return formatted_msg

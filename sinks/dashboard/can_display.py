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

BOARD_DATA = {"DUMMY": {"id": 0x00, "index": 0, "color": 'black', "msg_types": ["GENERAL_BOARD_STATUS", "GENERAL_CMD", "ACTUATOR_CMD", "ALT_ARM_CMD"]},
              "INJECTOR": {"id": 0x01, "index": 1, "color": 'chocolate', "msg_types": ["GENERAL_BOARD_STATUS", "ACTUATOR_STATUS"]},
              "LOGGER": {"id": 0x03, "index": 2, "color": 'darkCyan', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "RADIO": {"id": 0x05, "index": 3, "color": 'blue', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "SENSOR": {"id": 0x07, "index": 4, "color": 'darkblue', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "VENT": {"id": 0x0B, "index": 5, "color": 'slategray', "msg_types": ["GENERAL_BOARD_STATUS", "ACTUATOR_STATUS"]},
              "GPS": {"id": 0x0D, "index": 6, "color": 'darkMagenta', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "ARMING": {"id": 0x11, "index": 7, "color": 'darkGreen', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "PAPA": {"id": 0x13, "index": 8, "color": 'olive', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "ROCKET_PI": {"id": 0x15, "index": 9, "color": 'purple', "msg_types": ["GENERAL_BOARD_STATUS", "ACTUATOR_STATUS"]},
              "ROCKET_PI_2": {"id": 0x16, "index": 10, "color": 'deeppink', "msg_types": ["GENERAL_BOARD_STATUS", "ACTUATOR_STATUS"]},
              "SENSOR_2": {"id": 0x19, "index": 11, "color": 'steelblue', "msg_types": ["GENERAL_BOARD_STATUS"]},
              "SENSOR_3": {"id": 0x1B, "index": 12, "color": 'darkorange', "msg_types": ["GENERAL_BOARD_STATUS"]}}
CAN_MSG_TYPES = ["GENERAL_CMD",
                 "ACTUATOR_CMD",
                 "ALT_ARM_CMD",
                 "DEBUG_MSG",
                 "DEBUG_PRINTF",
                 "ALT_ARM_STATUS",
                 "ACTUATOR_STATUS",
                 "GENERAL_BOARD_STATUS",
                 "RECOVERY_STATUS",
                 "SENSOR_TEMP",
                 "SENSOR_ALTITUDE",
                 "SENSOR_ACC",
                 "SENSOR_ACC2",
                 "SENSOR_GYRO",
                 "SENSOR_MAG",
                 "SENSOR_ANALOG",
                 "GPS_TIMESTAMP",
                 "GPS_LATITUDE",
                 "GPS_LONGITUDE",
                 "GPS_ALTITUDE",
                 "GPS_INFO"]
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
        self.leftGrid = QtWidgets.QVBoxLayout()

        # create all buttons, labels and can nodes for each board id defined
        # add the above to the local layout (right for buttons/labels, left for terminals)
        for index, value in enumerate(list(BOARD_DATA.keys())):
            self.canNodes[index] = CanNodeWidgetDashItem(value)
            self.pushButtonList[index] = QtWidgets.QPushButton(value)
            self.pushButtonList[index].setCheckable(True)
            self.pushButtonList[index].setStyleSheet(
                f"color : {BOARD_DATA[value]['color']};")
            self.labels.append(QtWidgets.QLabel())
            # TODO: improve alignment
            self.rightGrid.addWidget(self.pushButtonList[index], index, QtCore.Qt.AlignCenter)
            self.rightGrid.addWidget(self.labels[index], index, QtCore.Qt.AlignCenter)
        self.layout.addLayout(self.rightGrid, 0, 1)
        self.layout.addLayout(self.leftGrid, 0, 0)

        self.setLayout(self.layout)

        # timer for updating the button/label states
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(100)

    def get_props(self):
        return self.props

    def update_board_health_state(self):
        """
        Updates the health status and color of each node
        """
        for node_name, node in self.canNodes.items():
            CAN_HEALTH_STATES[BOARD_DATA[node.boardId]["index"]] = node.boardStatus
            CAN_HEALTH_STATES_COLORS[BOARD_DATA[node.boardId]["index"]] = node.statusColor

    def add_node_widget(self, boardId):
        """
        Adds a CAN node to the set of text windows
        """
        self.canNodes[BOARD_DATA[boardId]["index"]].enable_terminal()
        self.textBrowsers[boardId] = {}
        self.textBrowsers[boardId]["widget"] = self.canNodes[BOARD_DATA[boardId]["index"]]
        self.leftGrid.addWidget(self.textBrowsers[boardId]["widget"].get_widget())
        self.browsersNextRow += 1

    def delete_node_widget(self, boardId):
        """
        Removes a CAN node to the set of text windows
        """
        self.leftGrid.removeWidget(self.textBrowsers[boardId]["widget"].get_widget())
        self.textBrowsers[boardId]["widget"].disable_terminal()
        del self.textBrowsers[boardId]
        self.browsersNextRow = len(self.textBrowsers)

    def update(self):
        """
        Updates running every 100ms for board health status, label states, and button states.
        Additionally, where the CAN node text windows get called to be created/deleted
        """
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

    def __init__(self, props=None, tableParent=None):
        super().__init__()
        self.props = props

        if self.props is None:
            # request boardId?
            self.boardId = "DUMMY"
        else:
            self.boardId = self.props

        self.tableParent = tableParent

        self.boardIndex = BOARD_DATA[self.boardId]['index']
        self.oldCanMsgTime = 0
        self.currCanMsgTime = 0
        self.msgHistoryQ = col.deque(maxlen=MAX_MSG_QUEUE_SIZE)

        # Start in dead status until we receive a message from this board
        self.boardStatus = "DEAD"
        self.statusColor = UNHEALTHY_STATE_COLOR

        self.textBrowser = None

        self.series = CanDisplayParser.get_canSeries(self.boardId)
        self.subscribe_to_series(self.series)

    def enable_terminal(self):
        """
        Create text window to display can messages for CAN node
        """
        self.textBrowser = QtWidgets.QTextBrowser()

    def disable_terminal(self):
        """
        Deletes CAN node's text window
        """
        self.textBrowser.clear()
        self.textBrowser.deleteLater()
        self.textBrowser = None

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.textBrowser

    def get_status_color(self, status):
        if status in ["E_NOMINAL", "RECEIVED_MSG_NO_STATUS"]:
            return HEALTHY_STATE_COLOR
        else:
            return UNHEALTHY_STATE_COLOR

    def get_formatted_msg(self, msg):
        formatted_msg = fmt_line(msg)
        return formatted_msg

    # TODO: fix implementation of updating health based on last received message time frame
    # def updateHealthChecks(self):
    #     """

    #     """
    #     # Check our last health check for this index was over 10s ago, now in DEAD state
    #     if self.currCanMsgTime < abs(self.oldCanMsgTime - HEALTHY_STATE_TIMEOUT):
    #         CAN_HEALTH_STATES[self.boardIndex] = "DEAD_FROM_TIMEOUT"
    #         CAN_HEALTH_STATES_COLORS[self.boardIndex] = UNHEALTHY_STATE_COLOR
    #     else:
    #         self.oldCanMsgTime = self.currCanMsgTime

    def updateCanMsgTimes(self, msg):
        self.currCanMsgTime = msg["data"]["time"]

    # Note: this function definitely doesn't have the most efficient solutions but prevents memory issues
    def on_data_update(self, series):
        # get the newest msg
        newestMsg = series.get_msg()
        # update some internal trackers
        self.updateCanMsgTimes(newestMsg)
        # self.updateHealthChecks()
        # check if our queue is already full, if so take off oldest msg
        if len(self.msgHistoryQ) == MAX_MSG_QUEUE_SIZE:
            self.msgHistoryQ.popleft()  # don't care about old message
        # put newest msg in queue
        self.msgHistoryQ.append(self.get_formatted_msg(newestMsg) + "\n")
        # update status
        if newestMsg["msg_type"] == "GENERAL_BOARD_STATUS":
            self.boardStatus = newestMsg["data"]["status"]
            self.statusColor = self.get_status_color(self.boardStatus)

        # update textBrowser if we are displaying in terminal
        if self.textBrowser is not None:
            # clear old text before pushing updated history
            self.textBrowser.clear()
            self.textBrowser.setTextColor(QtGui.QColor(BOARD_DATA[self.boardId]['color']))
            self.textBrowser.append("".join(str(ele) for ele in self.msgHistoryQ))

            # if scroll bar within 10 pixels of bottom, auto scroll to bottom
            scrollIsAtEnd = self.textBrowser.verticalScrollBar().maximum(
            ) - self.textBrowser.verticalScrollBar().value() <= 10
            if scrollIsAtEnd:
                self.textBrowser.verticalScrollBar().setValue(
                    self.textBrowser.verticalScrollBar().maximum())  # Scrolls to the bottom
        if self.tableParent is not None:
            self.tableParent.tableWidget.setItem(
                self.boardIndex, CAN_MSG_TYPES.index(newestMsg['msg_type']), QtWidgets.QTableWidgetItem(str(newestMsg['data'])))


class CanMsgTableDashItem(DashboardItem):
    """
    Display table for CAN messages.
    """

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        self.canNodes = {}

        self.tableWidget = QtWidgets.QTableWidget()
        self.tableWidget.setRowCount(len(BOARD_DATA))
        self.tableWidget.setColumnCount(len(CAN_MSG_TYPES))

        self.tableWidget.setVerticalHeaderLabels(BOARD_DATA.keys())
        self.tableWidget.setHorizontalHeaderLabels(CAN_MSG_TYPES)

        for row, board in enumerate(list(BOARD_DATA.keys())):
            self.canNodes[row] = CanNodeWidgetDashItem(board, self)
            for column, msg_type in enumerate(CAN_MSG_TYPES):
                if any(msg_type in value for value in BOARD_DATA[f'{board}']['msg_types']):
                    # TODO: do something to get board value
                    self.tableWidget.setItem(
                        row, column, QtWidgets.QTableWidgetItem("Value goes here..."))

        self.layout = QtWidgets.QVBoxLayout()
        self.layout.addWidget(self.tableWidget)
        self.setLayout(self.layout)

    def get_props(self):
        return self.props

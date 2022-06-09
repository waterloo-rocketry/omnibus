import signal
import queue as q

from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from dashboarditem import DashboardItem
from sources.parsley.parsley import fmt_line

# Main CAN message queue
CAN_MSGS = q.Queue()

# TODO: remove list below
BOARD_NAME_LIST = ["INJECTOR", "LOGGER", "RADIO", "SENSOR", "VENT",
                   "GPS", "ARMING", "TEMP_SENSE", "SENSOR_2", "SENSOR_3"]
# TODO: set better color schemes
BOARD_DATA = {"INJECTOR": {"id": 0x01, "index": 0, "color": QtGui.QColor('cyan')},
              "LOGGER": {"id": 0x03, "index": 1, "color": QtGui.QColor('darkCyan')},
              "RADIO": {"id": 0x05, "index": 2, "color": QtGui.QColor('red')},
              "SENSOR": {"id": 0x07, "index": 3, "color": QtGui.QColor('darkRed')},
              "VENT": {"id": 0x0B, "index": 4, "color": QtGui.QColor('magenta')},
              "GPS": {"id": 0x0D, "index": 5, "color": QtGui.QColor('darkMagenta')},
              "ARMING": {"id": 0x11, "index": 6, "color": QtGui.QColor('green')},
              "TEMP_SENSE": {"id": 0x15, "index": 7, "color": QtGui.QColor('darkGreen')},
              "SENSOR_2": {"id": 0x19, "index": 8, "color": QtGui.QColor('yellow')},
              "SENSOR_3": {"id": 0x1B, "index": 9, "color": QtGui.QColor('darkYellow')}}


class CanDisplayDashItem (DashboardItem):
    """
    Display for CAN messages.
    """

    def __init__(self, props=None):
        self.props = props

        self.BOARDS_TO_CHECK = [False] * len(BOARD_DATA)
        self.CAN_HEALTH_STATES = ["DEAD"] * len(BOARD_DATA)
        # last time reported from CAN node
        self.currCanNodeTime = 0
        self.canNodeTimeoutChecker = 0
        self.HEALTHY_STATE_TIMEOUT = 10000  # 10s
        self.currCanMsgTimes = [0] * len(BOARD_DATA)
        self.healthyCounter = 0

        self.groupbox = QtWidgets.QGroupBox("CAN Message Display")
        self.layout = QtWidgets.QGridLayout()

        self.textBroswers = {}
        self.browsersNextRow = 0

        self.pushButtonList = list(BOARD_DATA.keys())
        self.labels = []

        self.rightGrid = QtWidgets.QVBoxLayout()

        for index, value in enumerate(list(BOARD_DATA.keys())):
            self.pushButtonList[index] = QtWidgets.QPushButton(value)
            self.pushButtonList[index].setCheckable(True)
            self.labels.append(QtWidgets.QLabel())
            # TODO: improve alignment
            self.rightGrid.addWidget(self.pushButtonList[index], index, QtCore.Qt.AlignCenter)
            self.rightGrid.addWidget(self.labels[index], index, QtCore.Qt.AlignCenter)
        self.layout.addLayout(self.rightGrid, 0, 1)
        self.groupbox.setLayout(self.layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.updateHealthChecks)
        self.timer.start(1000)

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.groupbox

    def updateHealthChecks(self):
        for index, value in enumerate(self.CAN_HEALTH_STATES):
            # No point processing indexes whose health states we don't care about
            if self.BOARDS_TO_CHECK[index]:
                # Check our last health check for this index was over 10s ago, now in DEAD state
                if self.currCanMsgTimes[index] < abs(self.currCanNodeTime - self.HEALTHY_STATE_TIMEOUT):
                    self.CAN_HEALTH_STATES[index] = "DEAD"
                else:
                    self.CAN_HEALTH_STATES[index] = "HEALTHY"

    def updateCanMsgTimes(self, msg):
        try:
            boardIndex = BOARD_DATA[msg['board_id']]['index']
        except KeyError:
            # board ID we don't have implemented
            pass

        self.currCanMsgTimes[boardIndex] = msg["data"]["time"]

        # Update radio board's times too because if we received a message, it passed a health check
        self.currCanMsgTimes[BOARD_DATA['RADIO']['index']] = msg["data"]["time"]

    def get_board_health_state(self, index):
        return self.CAN_HEALTH_STATES[index]

    def update(self):
        if not CAN_MSGS.empty():
            msg = CAN_MSGS.get()
            self.updateCanMsgTimes(msg)
            for value in self.textBroswers.values():
                value.update(msg)
        for index, value in enumerate(self.pushButtonList):
            self.labels[index].setText(self.get_board_health_state(index)
                                       if value.isChecked() else "N/A")

            node_name = BOARD_NAME_LIST[index]
            if value.isChecked():
                self.BOARDS_TO_CHECK[index] = True
                if node_name not in self.textBroswers.keys():
                    new_node = CanNodeWidgetDashItem(props=[node_name])
                    self.textBroswers[node_name] = new_node
                    self.layout.addWidget(
                        self.textBroswers[node_name].get_widget(), self.browsersNextRow, 0)
                    self.browsersNextRow += 1
            elif node_name in self.textBroswers.keys():
                self.layout.removeWidget(self.textBroswers[node_name].get_widget())
                self.textBroswers[node_name].get_widget().deleteLater()
                del self.textBroswers[node_name]
                self.browsersNextRow = len(self.textBroswers)


class CanNodeWidgetDashItem:
    """
    Display for CAN messages.
    """

    def __init__(self, props=None):
        self.props = props

        if self.props is None:
            # request board_id?
            self.board_id = "DUMMY"
        else:
            self.board_id = self.props[0]

        self.textBrowser = QtWidgets.QTextBrowser()

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.textBrowser

    def get_formatted_msg(self, msg):
        formatted_msg = fmt_line(msg)
        return formatted_msg

    def update(self, msg):
        print(f"msg: {msg}\n")
        if msg['board_id'] == self.board_id:
            self.textBrowser.setTextColor(BOARD_DATA[msg['board_id']]['color'])
            self.textBrowser.append(str(self.get_formatted_msg(msg)))

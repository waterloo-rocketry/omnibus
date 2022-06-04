import signal
import queue as q

from pyqtgraph.Qt import QtCore, QtWidgets

from dashboarditem import DashboardItem

# Main CAN message queue
CAN_MSGS = q.Queue()
BOARD_IDS = {"INJECTOR": 0, "LOGGER": 1, "RADIO": 2, "SENSOR": 3, "VENT": 4,
             "GPS": 5, "FILL": 6, "ARMING": 7, "TEMP_SENSE": 8, "PICAM_1": 9, "PICAM_2": 10}


class CanDisplayDashItem (DashboardItem):
    """
    Display for CAN messages.
    """

    def __init__(self, props=None):
        self.props = props

        self.BOARDS_TO_CHECK = [False] * len(BOARD_IDS)
        self.CAN_HEALTH_STATES = ["DEAD"] * len(BOARD_IDS)
        # last time reported from CAN node
        self.currCanNodeTime = 0
        self.canNodeTimeoutChecker = 0
        self.HEALTHY_STATE_TIMEOUT = 10000  # 10s
        self.currCanMsgTimes = [0] * len(BOARD_IDS)
        self.healthyCounter = 0

        self.groupbox = QtWidgets.QGroupBox("CAN Message Display")
        self.layout = QtWidgets.QHBoxLayout()

        self.textBrowser = QtWidgets.QTextBrowser()
        self.layout.addWidget(self.textBrowser)

        self.checkboxList = list(BOARD_IDS.keys())
        self.labels = []

        self.rightGrid = QtWidgets.QVBoxLayout()

        for index, value in enumerate(list(BOARD_IDS.keys())):
            self.checkboxList[index] = QtWidgets.QCheckBox(value)
            self.labels.append(QtWidgets.QLabel())
            # TODO: improve alignment
            self.rightGrid.addWidget(self.checkboxList[index], index, QtCore.Qt.AlignCenter)
            self.rightGrid.addWidget(self.labels[index], index, QtCore.Qt.AlignCenter)
        self.layout.addLayout(self.rightGrid)
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
            boardIndex = BOARD_IDS[f"{msg['board_id']}"]
        except KeyError:
            # board ID we don't have implemented
            pass

        self.currCanMsgTimes[boardIndex] = msg["data"]["time"]

        # Update radio board's times too because if we received a message, it passed a health check
        self.currCanMsgTimes[BOARD_IDS["RADIO"]] = msg["data"]["time"]

    def get_board_health_state(self, index):
        return self.CAN_HEALTH_STATES[index]

    def update(self):
        if not CAN_MSGS.empty():
            msg = CAN_MSGS.get()
            self.updateCanMsgTimes(msg)
            if (self.checkboxList[BOARD_IDS[msg['board_id']]].checkState()):
                self.textBrowser.append(str(msg))
        for index, value in enumerate(self.checkboxList):
            self.labels[index].setText(self.get_board_health_state(index)
                                       if value.checkState() else "N/A")
            if value.checkState():
                self.BOARDS_TO_CHECK[index] = True

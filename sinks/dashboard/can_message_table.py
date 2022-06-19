from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import sys
from dashboarditem import DashboardItem
from parsers import CanDisplayParser

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
    CAN Message. Makes use of a QTable
	"""
	def __init__(self):
		# Super Class Init
		super().__init__()
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.tableWidget = QtWidgets.QTableWidget()
		# 8 bytes, 3 used by time stamp leaves 6 total fields
		# + 1 title field
		self.tableWidget.setRowCount(7) 
		self.tableWidget.setColumnCount(2 * len(CAN_MSG_TYPES))

		for i in range(len(CAN_MSG_TYPES)):
			self.tableWidget.setSpan(0, 2*i, 1, 2)
			self.tableWidget.setItem(0, 2*i, QtWidgets.QTableWidgetItem(CAN_MSG_TYPES[i]))

		self.layout.addWidget(self.tableWidget)


	def update_with_message(self, msg):
		msg_type = msg["msg_type"]
		msg_data = msg["data"]

		index = -1

		for i in range(len(CAN_MSG_TYPES)):
			if CAN_MSG_TYPES[i] == msg_type:
				index = i

		for i, (k, v) in enumerate(msg_data.items()):
			self.tableWidget.setItem(i+1, 2*index, QtWidgets.QTableWidgetItem(str(k)))
			self.tableWidget.setItem(i+1, 2*index + 1, QtWidgets.QTableWidgetItem(str(v)))


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

		menubar = QtGui.QMenuBar(self)
		self.layout.setMenuBar(menubar)

		self.content = widget
		self.is_expanded = False

		self.expand_contract_action = menubar.addAction(f"> {self.name}")
		self.expand_contract_action.triggered.connect(self.toggle)

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


class CanMsgTableDashItem(DashboardItem):
    """
    Display table for CAN messages.
    """

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        # 1) Establish a structure of one expanding 
        #    widget per board
        # 2) For each of those widgets, add a Display
        #    object for each message type
        # 3) set the update function up in such a
        #    way that when a message is recieved, it
        #    is rendered in the right object

        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        self.message_dict = {}
        # Each key is  board ID
        # Each value is another dictionary
        # within the second dictionary, each 
        # key is a message type and the value is the
        # specific DisplayObject

        board = list(BOARD_DATA.keys())[0]
        table = DisplayCANTable()
        self.message_dict[board] = table
        exp_widget = ExpandingWidget(board, table)
        self.layout.addWidget(exp_widget)

        # Subscribe to all relavent series
        for series in CanDisplayParser.get_all_series():
        	self.subscribe_to_series(series)

    def get_props(self):
        return self.props

    def on_data_update(self, canSeries):
    	message = canSeries.get_msg()
    	if canSeries.name in self.message_dict:
    		self.message_dict[canSeries.name].update_with_message(message)

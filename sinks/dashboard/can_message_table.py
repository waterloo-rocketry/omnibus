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


class DisplayObject(QtWidgets.QWidget):
	"""
	A widget that displays an object, in our case a 
    CAN Message. Makes use of a QTable
	"""
	def __init__(self, object=None):
		# Super Class Init
		super().__init__()
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.tableWidget = QtWidgets.QTableWidget()
		self.set_object(object)

	def set_object(self, object):
		self.tableWidget.deleteLater()
		del self.tableWidget

		self.tableWidget = QtWidgets.QTableWidget()

		if not isinstance(object, dict):
			object = None
		elif object == None:
			self.tableWidget.setRowCount(1)
			self.tableWidget.setColumnCount(1)
			self.tableWidget.setItem(0, 0, QtWidgets.QTableWidgetItem("None"))
		else:
			self.tableWidget.setRowCount(len(object))
			self.tableWidget.setColumnCount(1)

			self.tableWidget.setVerticalHeaderLabels(object.keys())

			for i, value in enumerate(object.values()):
				self.tableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(str(value)))

		self.layout.addWidget(self.tableWidget)

class GridLayoutWidget(QtWidgets.QWidget):
	"""
	Just a adaptor on QGridLayout
	"""
	def __init__(self):
		super().__init__()
		self.layout = QtWidgets.QGridLayout()
		self.setLayout(self.layout)

	def add_widget(self, widget, row, col):
		self.layout.addWidget(widget, row, col)

	def remove_widget(self, widget):
		self.layout.removeWidget(widget)


class ExpandingWidget(QtWidgets.QWidget):
	"""
	A widget whose sole function is to contain a
	grid layout and expand and collapse on click
	"""
	def __init__(self, name):
		super().__init__()
		self.layout = QtWidgets.QVBoxLayout()
		self.setLayout(self.layout)

		self.name = name

		menubar = QtGui.QMenuBar(self)
		self.layout.setMenuBar(menubar)

		self.content = GridLayoutWidget()
		self.is_expanded = False

		self.expand_contract_action = menubar.addAction(f"> {self.name}")
		self.expand_contract_action.triggered.connect(self.toggle)

	def toggle(self):
		if self.is_expanded:
			self.layout.removeWidget(self.content)
			self.expand_contract_action.setText(f"> {self.name}")
		else:
			self.layout.addWidget(self.content)
			self.expand_contract_action.setText(f"V {self.name}")


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

        for board in BOARD_DATA:
        	self.message_dict[board] = {}
        	table = ExpandingWidget(board)

        	for i, message_type in enumerate(CAN_MSG_TYPES):
        		display_object = DisplayObject()
        		table.content.add_widget(display_object, 0, i)
        		self.message_dict[board][message_type] = display_object

        	self.layout.addWidget(table)

        # Subscribe to all relavent series
        for series in CanDisplayParser.get_all_series():
        	self.subscribe_to_series(series)

    def get_props(self):
        return self.props

    def on_data_update(self, canSeries):
    	message = canSeries.get_msg()
    	tpe = message["msg_type"]
    	message.pop("msg_type", None)
    	self.message_dict[canSeries.name][tpe].set_object(message)

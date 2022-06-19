from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import sys
from dashboarditem import DashboardItem

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
		print("ran")
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

		menubar = QMenuBar(self)
		self.layout.setMenuBar(menubar)

		self.content = GridLayoutWidget()
		self.is_expanded = False

		self.expand_contract_action = menubar.addAction("Expand")
		self.expand_contract_action.triggered.connect(self.toggle)

	def toggle(self):
		if self.is_expanded:
			self.layout.removeWidget(self.content)
			self.expand_contract_action.setText("Expand")
		else:
			self.layout.addWidget(self.content)
			self.expand_contract_action.setText("Contract")


class CanMsgTableDashItem(DashboardItem):
    """
    Display table for CAN messages.
    """

    def __init__(self, props=None):
        super().__init__()
        self.props = props

        

    def get_props(self):
        return self.props

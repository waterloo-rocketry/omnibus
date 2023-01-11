from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QVBoxLayout
from pyqtgraph.Qt.QtGui import QPixmap

from .dashboard_item import DashboardItem
from .registry import Register


class ImageDashItem(DashboardItem):
    def __init__(self, imgPath):
        # Call this in **every** dash item constructor
        super().__init__()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.imgPath = imgPath

        self.picture = QPixmap(self.imgPath)
        self.picWidget = QtWidgets.QLabel()
        self.picWidget.setPixmap(self.picture)
        self.layout.addWidget(self.picWidget)
        self.layout.addWidget(QtWidgets.QLabel(self.imgPath))
        

    def on_delete(self):
        pass

    def get_name(self):
        return self.imgPath

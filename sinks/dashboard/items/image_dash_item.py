from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QVBoxLayout
from pyqtgraph.Qt.QtGui import QPixmap
from pyqtgraph.Qt.QtCore import Qt

from .dashboard_item import DashboardItem

import time

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
        self.layout.addWidget(self.picWidget, alignment=Qt.AlignmentFlag.AlignTop)
        self.labelWidget = QtWidgets.QLabel(self.imgPath)
        self.layout.addWidget(self.labelWidget, alignment=Qt.AlignmentFlag.AlignBottom)
        
        self.w = self.width()
        self.h = self.height()

    def on_delete(self):
        pass

    def get_name(self):
        return self.imgPath

    # Honestly? This is a hard-coded and very scuffed solution. It doesn't even come with aspect ratio preservation. Don't use this lest we have no solutions.
    def resizeEvent(self, event):
        time.sleep(0.0000001)
        self.picture = QPixmap(self.imgPath).scaled(self.width() - 40, self.height() - self.labelWidget.height() - 40)
        self.picWidget.setPixmap(self.picture)

        QtWidgets.QWidget.resizeEvent(self, event)

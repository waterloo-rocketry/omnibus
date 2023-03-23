from pyqtgraph.Qt.QtWidgets import QGridLayout, QMenu, QFileDialog, QLabel
from pyqtgraph.Qt.QtGui import QPixmap

from PySide6 import QtCore

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class ImageDashItem(DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # save props as a field
        self.props = props if props else {"path": ""}

        self.widget = QLabel(self)
        self.widget.setPixmap(QPixmap(self.props["path"]).scaledToWidth(self.width() - 30))

        self.layout.addWidget(self.widget, 0, 0)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        change_threshold = menu.addAction('Change image')

        action = menu.exec_(event.globalPos())
        if action == change_threshold:
            self.props = self.prompt_for_properties()
            self.widget.setPixmap(QPixmap(self.props["path"]).scaledToWidth(self.width() - 30))

    def resizeEvent(self, event):
        newWidth = event.size().width() - 30
        newHeight = event.size().height() - 30
        newPix = QPixmap(self.props["path"]).scaled(newWidth, newHeight, QtCore.Qt.KeepAspectRatio)
        self.widget.setPixmap(newPix)

    def prompt_for_properties(self):
        open_to = self.get_props().get("path", "")
        (name, _) = QFileDialog.getOpenFileName(self,
                                                'Open File',
                                                open_to,
                                                'Image Files (*.png *.jpg *.bmp *.gif *.jpeg)')
        if name:
            props = {"path": name}
            return props
        return None

    def get_props(self):
        return self.props

    @staticmethod
    def get_name():
        return "Image"

from pyqtgraph.Qt.QtWidgets import QHBoxLayout
from pyqtgraph.Qt.QtCore import QRect
from pyqtgraph.Qt.QtGui import QPixmap, QPainter
from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QWidget
from pyqtgraph.parametertree.parameterTypes import FileParameter

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class ImageDashItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # need to wrap the label in a scroll area to
        # avoid problems by qt widget resizing on text change
        self.widget = ImageWidget(self)
        self.resize(100, 100)

        self.image_path = self.parameters.child("file").value()
        self.pixmap = None

        if self.image_path:
            self.on_file_change()

        self.parameters.sigTreeStateChanged.connect(self.on_file_change)

        self.layout.addWidget(self.widget)

    def add_parameters(self):
        # list of supported file formats: https://doc.qt.io/qtforpython-5/PySide2/QtGui/QImageReader.html#PySide2.QtGui.PySide2.QtGui.QImageReader.supportedImageFormats
        file_param = FileParameter(name="file", value="", nameFilter="*.jpg;*.png;*.svg")
        return [file_param]

    def on_file_change(self):
        self.image_path = self.parameters.child("file").value()
        self.pixmap = QPixmap(self.image_path)

    @staticmethod
    def get_name():
        return "Image"


class ImageWidget(QWidget):
    def __init__(self, item: ImageDashItem):
        super().__init__()
        self.item: ImageDashItem = item

    def paintEvent(self, paintEvent):
        width = self.width()
        height = self.height()

        if self.item.pixmap is None:
            return
        
        with QPainter(self) as painter:
            painter.drawPixmap(QRect(0, 0, width, height), self.item.pixmap, QRect(0, 0, self.item.pixmap.width(), self.item.pixmap.height()))

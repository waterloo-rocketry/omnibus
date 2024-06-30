from pyqtgraph.Qt.QtWidgets import QHBoxLayout
from pyqtgraph.Qt.QtCore import QRect, QRectF
from pyqtgraph.Qt.QtGui import QImage, QPainter
from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QWidget
from pyqtgraph.parametertree.parameterTypes import FileParameter

from .dashboard_item import DashboardItem
from .no_text_action_parameter import NoTextActionParameter
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
        self.image = None

        if self.image_path:
            self.on_file_change()

        self.parameters.param("file").sigTreeStateChanged.connect(self.on_file_change)
        self.parameters.param("original_size").sigActivated.connect(self.set_original_size)

        self.layout.addWidget(self.widget)

    def add_parameters(self):
        # list of supported file formats: https://doc.qt.io/qtforpython-5/PySide2/QtGui/QImageReader.html#PySide2.QtGui.PySide2.QtGui.QImageReader.supportedImageFormats
        file_param = FileParameter(name="file", value="", nameFilter="*.jpg;*.png;*.svg")
        original_size = NoTextActionParameter(name="original_size")
        return [file_param, original_size]

    def on_file_change(self):
        self.image_path = self.parameters.child("file").value()
        self.image = QImage(self.image_path)
        self.set_original_size()
        self.widget.update()

    def set_original_size(self):
        if self.image is not None:
            self.resize(self.image.width(), self.image.height())
        else:
            self.resize(100, 100)

    @staticmethod
    def get_name():
        return "Image"


class ImageWidget(QWidget):
    def __init__(self, item: ImageDashItem):
        super().__init__()
        self.item: ImageDashItem = item

    def paintEvent(self, paintEvent):
        if self.item.image is None:
            return
        
        width = self.width()
        height = self.height()
        image_width = self.item.image.width()
        image_height = self.item.image.height()

        render_width = min(width, height / image_height * image_width)
        render_height = min(height, width / image_width * image_height)
        
        with QPainter(self) as painter:
            painter.drawImage(QRectF((width - render_width) / 2, (height - render_height) / 2, render_width, render_height), self.item.image, QRect(0, 0, image_width, image_height))

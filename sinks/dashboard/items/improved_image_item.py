from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QFileDialog, QLayout, QSizePolicy
from pyqtgraph.Qt.QtGui import QPixmap
from pyqtgraph.parametertree.parameterTypes import FileParameter
from pyqtgraph.Qt.QtCore import QSize, Qt

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class ImprovedImageItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        # self.layout.setSizeConstraint(QLayout.SetFixedSize)

        self.widget = QLabel()
        self.widget.setAlignment(Qt.AlignCenter)
        self.widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.widget.setScaledContents(True)

        # if we set the size of image same as the widget, the widget will
        # grow, triggering the resize event which makes an infinite loop
        # this is a hacky way to avoid that and the value is achieved using
        # trial and error
        self.offset = 40

        self.parameters.child("height").setReadonly()
        self.parameters.child("width").setValue(300)
        self.parameters.child("height").setValue(300)
        self.image_path = QFileDialog.getOpenFileName(self, "Open Image", "~/", "Image Files (*.png *.jpg *.svg)")[0]
        self.parameters.child("file").setValue(self.image_path)

        self.parameters.child("width").sigStateChanged.connect(self.on_file_change)
        self.parameters.child("file").sigStateChanged.connect(self.on_file_change)
        self.on_file_change()
        self.layout.addWidget(self.widget)

    def add_parameters(self):
        file_param = FileParameter(name="file", value="", nameFilter="*.jpg;*.png;*.svg")
        return [file_param]

    def on_file_change(self):
        width = self.parameters.child("width").value() - self.offset
        self.image_path = self.parameters.child("file").value()
        self.pixmap = QPixmap(self.image_path).scaledToWidth(width)
        height = self.pixmap.height() + self.offset
        self.parameters.child("height").setValue(height)
        self.widget.setPixmap(self.pixmap)
        self.resize(width, height)

    @staticmethod
    def get_name():
        return "BetterImage"

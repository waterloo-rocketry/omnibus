from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QScrollArea
from pyqtgraph.Qt.QtGui import QPixmap
from pyqtgraph.parametertree.parameterTypes import FileParameter
from pyqtgraph.Qt.QtCore import QSize, Qt

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class ImageDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # need to wrap the label in a scroll area to
        # avoid problems by qt widget resizing on text change
        self.widget = QLabel()
        self.frame = QScrollArea()
        self.frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frame.setWidgetResizable(True)
        self.frame.setWidget(self.widget)

        self.image_path = self.parameters.child("file").value()

        # if we set the size of image same as the widget, the widget will
        # grow, triggering the resize event which makes an infinite loop
        # this is a hacky way to avoid that and the value is achieved using
        # trial and error
        self.offset = 40

        if self.image_path:
            width = self.parameters.child("width").value() - self.offset # subtracting here to account
            height = self.parameters.child("height").value() - self.offset # for the new "border"
            self.widget.setPixmap(QPixmap(self.image_path).scaled(width, height))

        self.parameters.sigTreeStateChanged.connect(self.on_file_change)

        self.layout.addWidget(self.frame)

    def add_parameters(self):
        file_param = FileParameter(name="file", value="")
        return [file_param]

    def on_file_change(self):
        width = self.parameters.child("width").value() - self.offset
        height = self.parameters.child("height").value() - self.offset
        self.image_path = self.parameters.child("file").value()

        self.widget.setPixmap(QPixmap(self.image_path).scaled(width, height))

    @staticmethod
    def get_name():
        return "Image"

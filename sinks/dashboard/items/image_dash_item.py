from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel
from pyqtgraph.Qt.QtGui import QPixmap
from pyqtgraph.parametertree.parameterTypes import FileParameter
from pyqtgraph.Qt.QtCore import QSize

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

        self.widget = QLabel()
        self.image_path = self.parameters.child("file").value()

        # if we set the size of image same as the widget, the widget will
        # grow, triggering the resize event which makes an infinite loop
        # this is a hacky way to avoid that and the value is achieved using
        # trial and error
        self.offset = 50

        if self.image_path:
            width = self.parameters.child("width").value() - self.offset # subtracting here to account
            height = self.parameters.child("height").value() - self.offset # for the new "border"
            self.widget.setPixmap(QPixmap(self.image_path).scaled(width, height))

        self.parameters.sigTreeStateChanged.connect(self.on_file_change)

        self.layout.addWidget(self.widget)


    def add_parameters(self):
        file_param = FileParameter(name="file", value="")
        return [file_param]

    def on_file_change(self):
        width = self.parameters.child("width").value() - self.offset
        height = self.parameters.child("height").value() - self.offset
        self.image_path = self.parameters.child("file").value()
        self.widget.setPixmap(QPixmap(self.image_path).scaled(width, height))
        self.widget.frameGeometry().setSize(QSize(width, height))
        print("on_file_change", width, height)
        # self.widget.setMargin(10)
        # self.widget.setText("AAAAA")

    def update_dimensions(self):
        bounding_rect = self.widget.fontMetrics().boundingRect(self.text)
        print("bounding_rect", bounding_rect.width(), bounding_rect.height())
        with self.parameters.treeChangeBlocker():
            self.parameters.child('width').setValue(bounding_rect.width() + 5)
            self.parameters.child('height').setValue(bounding_rect.height() + 5)


    def minimumSize(self):
        # width = self.parameters.child('width').value()
        # height = self.parameters.child('height').value()
        # return QSize(width, height)
        return QSize(1, 1)

    @staticmethod
    def get_name():
        return "Image"

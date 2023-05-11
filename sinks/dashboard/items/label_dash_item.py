from pyqtgraph.Qt.QtWidgets import QGridLayout, QLabel
from pyqtgraph.Qt.QtCore import QSize

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class LabelDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        self.text = self.parameters.param('text').value()
        self.fsize = self.parameters.param('fsize').value()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.widget = QLabel()
        self.widget.setScaledContents(True)
        self.widget.setFrameStyle(QLabel.NoFrame)

        if self.text:
            self.widget.setText(self.text)
            self.setFontSize(self.fsize)

        self.parameters.param('text').sigValueChanged.connect(self.on_text_change)
        self.parameters.param('fsize').sigValueChanged.connect(self.on_fsize_change)

        self.layout.addWidget(self.widget, 0, 0)

    def setFontSize(self, fsize):
        self.fsize = fsize
        self.widget.setStyleSheet("font-size: {}px; color: blue; background-color: white; padding: 3px".format(self.fsize))

    def add_parameters(self):
        text_param = {'name': 'text', 'type': 'str', 'value': ''}
        fsize_param = {'name': 'fsize', 'type': 'int', 'value': 12}
        return [text_param, fsize_param]

    def on_text_change(self, param, value):
        self.text = value
        self.widget.setText(self.text)
        self.update_dimensions()

    def on_fsize_change(self, param, value):
        self.setFontSize(value)
        self.update_dimensions()

    def update_dimensions(self):
        bounding_rect = self.widget.fontMetrics().boundingRect(self.text)
        # print("bounding_rect", bounding_rect.width(), bounding_rect.height())
        # print("frameGeometry", self.widget.frameGeometry().width(), self.widget.frameGeometry().height())
        with self.parameters.treeChangeBlocker():
            self.parameters.child('width').setValue(bounding_rect.width() + 5)
            self.parameters.child('height').setValue(bounding_rect.height() + 5)

    def minimumSize(self):
        return QSize(1, 1)

    @staticmethod
    def get_name():
        return "Text"

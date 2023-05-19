from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QScrollArea
from pyqtgraph.Qt.QtCore import QSize, Qt

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class TextDashItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        self.text = self.parameters.param('text').value()
        self.fsize = self.parameters.param('fsize').value()

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # need to wrap the label in a scroll area to
        # avoid problems by qt widget resizing on text change
        self.widget = QLabel()

        self.setFontSize(self.fsize)
        if self.text:
            self.widget.setText(self.text)

        self.parameters.param('text').sigValueChanged.connect(self.on_text_change)
        self.parameters.param('fsize').sigValueChanged.connect(self.on_fsize_change)

        self.layout.addWidget(self.widget)

    def setFontSize(self, fsize):
        self.fsize = fsize
        self.widget.setStyleSheet(f"font-size: {self.fsize}px")

    def add_parameters(self):
        text_param = {'name': 'text', 'type': 'str', 'value': ''}
        fsize_param = {'name': 'fsize', 'type': 'int', 'value': 12}
        return [text_param, fsize_param]

    def on_text_change(self, param, value):
        self.text = value
        self.widget.setText(self.text)
        self.resize(10, 10) # update size

    def on_fsize_change(self, param, value):
        self.setFontSize(value)

    @staticmethod
    def get_name():
        return "Text"

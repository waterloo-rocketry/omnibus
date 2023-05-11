from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel, QScrollArea
from pyqtgraph.Qt.QtCore import QSize, Qt

from .dashboard_item import DashboardItem
from .registry import Register


@Register
class TextDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        self.text = self.parameters.param('text').value()
        self.fsize = self.parameters.param('fsize').value()

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        # need to wrap the label in a scroll area to
        # avoid problems by qt widget resizing on text change
        self.widget = QLabel()
<<<<<<< HEAD
        self.widget.setAlignment(Qt.AlignCenter)
=======
>>>>>>> 2399007 (add new widgets)
        self.frame = QScrollArea()
        self.frame = QScrollArea()
        self.frame.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frame.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.frame.setWidgetResizable(True)
        self.frame.setWidget(self.widget)

        self.setFontSize(self.fsize)
        if self.text:
            self.widget.setText(self.text)

        self.parameters.param('text').sigValueChanged.connect(self.on_text_change)
        self.parameters.param('fsize').sigValueChanged.connect(self.on_fsize_change)

        self.layout.addWidget(self.frame)

    def setFontSize(self, fsize):
        self.fsize = fsize
<<<<<<< HEAD
        self.widget.setStyleSheet(
            "font-size: {}px; color: blue; background-color: white".format(self.fsize))
=======
        self.widget.setStyleSheet("font-size: {}px; color: blue; background-color: white".format(self.fsize))
>>>>>>> 2399007 (add new widgets)

    def add_parameters(self):
        text_param = {'name': 'text', 'type': 'str', 'value': ''}
        fsize_param = {'name': 'fsize', 'type': 'int', 'value': 30}
        return [text_param, fsize_param]

<<<<<<< HEAD
    def on_text_change(self, param, value):
        self.text = value
        self.widget.setText(self.text)

    def on_fsize_change(self, param, value):
=======
    def on_text_change(self, _, value):
        self.text = value
        self.widget.setText(self.text)

    def on_fsize_change(self, _, value):
>>>>>>> 2399007 (add new widgets)
        self.setFontSize(value)

    @staticmethod
    def get_name():
        return "Text"

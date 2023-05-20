from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel
from pyqtgraph.Qt.QtCore import QTimer
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 1  # time in seconds after which data "expires"


@Register
class DynamicTextItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.parameters.param('font size').sigValueChanged.connect(self.on_font_change)
        self.parameters.param('offset').sigValueChanged.connect(self.on_offset_change)
        self.parameters.param('buffer size').sigValueChanged.connect(self.on_buffer_size_change)

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(EXPIRED_TIME * 1000)

        series = self.parameters.param('series').value()
        self.offset = self.parameters.param('offset').value()
        publisher.subscribe(series, self.on_data_update)

        self.widget = QLabel()
        self.layout.addWidget(self.widget)

        # Apply initial stylesheet
        self.on_font_change(None, self.parameters.param("font size").value())

        self.buffer_size = self.parameters.param('buffer size').value()
        self.buffer = []

    def add_parameters(self):
        font_param = {'name': 'font size', 'type': 'int', 'value': 12}
        series_param = ListParameter(name='series',
                                          type='list',
                                          default="",
                                          limits=publisher.get_all_streams())
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0}
        buffer_size_param = {'name': 'buffer size', 'type': 'int', 'value': 1}
        return [font_param, series_param, offset_param, buffer_size_param]

    def on_series_change(self, _, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        publisher.subscribe(value, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload

        self.buffer.append(data)
        if len(self.buffer) > self.buffer_size:
            self.buffer.pop(0)

        if isinstance(data, int):
            value = sum(self.buffer)/len(self.buffer)
            self.widget.setText(f"{value + self.offset:.0f}")
        elif isinstance(data, float):
            value = sum(self.buffer)/len(self.buffer)
            self.widget.setText(f"{value + self.offset:.3f}")
        else:
            self.widget.setText(str(data))
        self.setStyleSheet("")
        self.expired_timeout.stop()
        self.expired_timeout.start(EXPIRED_TIME * 1000)
        self.resize(10, 10)  # trigger size update

    def expire(self):
        self.setStyleSheet("color: gray")

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet(f"font-size: {fsize}px")

    def on_offset_change(self, _, offset):
        self.offset = offset

    def on_buffer_size_change(self, _, bufsize):
        self.buffer_size = bufsize
        self.buffer = []


    @staticmethod
    def get_name():
        return "Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel
from pyqtgraph.Qt.QtCore import QTimer
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 1 # time in seconds after which data "expires"


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

    def add_parameters(self):
        font_param =  {'name': 'font size', 'type': 'int', 'value': 12}
        series_param = ListParameter(name='series',
                                          type='list',
                                          default="",
                                          limits=publisher.get_all_streams())
        offset_param =  {'name': 'offset', 'type': 'float', 'value': 0}
        return [font_param, series_param, offset_param]

    def on_series_change(self, _, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        publisher.subscribe(value, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload
        if isinstance(data, int):
            self.widget.setText(f"{data + self.offset:.0f}")
        elif isinstance(data, float):
            self.widget.setText(f"{data + self.offset:.3f}")
        else:
            self.widget.setText(str(data))
        self.setStyleSheet("")
        self.expired_timeout.stop()
        self.expired_timeout.start(EXPIRED_TIME * 1000)
        self.resize(10, 10) # trigger size update

    def expire(self):
        self.setStyleSheet("color: gray")

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet("font-size: {}px".format(fsize))

    def on_offset_change(self, _, offset):
        self.offset = offset

    @staticmethod
    def get_name():
        return "Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

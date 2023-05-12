from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QLabel
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register


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

        series = self.parameters.param('series').value()
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
        return [font_param, series_param]

    def on_series_change(self, _, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        publisher.subscribe(value, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload
        if isinstance(data, float):
            self.widget.setText(f"{data:.3f}")
        else:
            self.widget.setText(str(data))
        self.resize(10, 10) # trigger size update

    def on_font_change(self, _, fsize):
        self.widget.setStyleSheet("font-size: {}px".format(fsize))

    @staticmethod
    def get_name():
        return "Dynamic Text"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

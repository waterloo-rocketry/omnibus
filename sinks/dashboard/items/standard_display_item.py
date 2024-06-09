from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register
from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QWidget, QLabel
import pyqtgraph as pg

@Register
class StandardDisplayItem (DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.text = self.parameters.param('text').value()

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Medium text label
        self.label = QLabel()
        

        # Value detection based on plot_dah_item.py
        self.parameters.param('text').sigValueChanged.connect(self.on_label_change)

        self.layout.addWidget(self.label)
        

    def add_parameters(self):
        text_param = {'name': 'text', 'type': 'str', 'value': ''}
        return [text_param]
    
    def on_label_change(self, param, value):
        self.text = value
        self.label.setText(self.text)
        self.resize(10,10)

    @staticmethod
    def get_name():
        return "Standard Display Item"
    
    def on_delete(self):
        publisher.unsusbcribe_from_all(self.on_data_update)
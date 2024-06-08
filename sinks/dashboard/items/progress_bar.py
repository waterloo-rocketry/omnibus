from publisher import publisher
from PySide6.QtGui import QLinearGradient, QColor, QBrush
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtGui import QBrush, QFont, QPainter
from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QWidget
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter

from .dashboard_item import DashboardItem
from .registry import Register

@Register
class ProgressBarItem(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.widget = ProgressBarWidget(self)
        self.layout.addWidget(self.widget)

        self.resize(200, 80) # Change the initial size of the progress bar

        # Value detection code is based on plot_dash_item.py
        self.parameters.param("value").sigValueChanged.connect(self.on_value_change)

        self.parameters.param("min_value").sigValueChanged.connect(
            self.on_min_value_change
        )
        self.parameters.param("max_value").sigValueChanged.connect(
            self.on_max_value_change
        )
        self.parameters.param("label").sigValueChanged.connect(self.on_label_change)

        self.data: float = 0.0

        self.min_value: float = 0.0
        self.max_value: float = 10.0
        self.label = ""
        self.value = "Not connected"

        # Initialize with 70% progress
        # self.data = (self.max_value+self.min_value)*0.7
        # self.update_data()

    def add_parameters(self):
        value_param = ChecklistParameter(
            name="value",
            type="list",
            value=[],
            limits=publisher.get_all_streams(),
            exclusive=True,
        )
        min_value_param = {"name": "min_value", "type": "float", "value": 0.0}
        max_value_param = {"name": "max_value", "type": "float", "value": 10.0}
        label_param = {"name": "label", "type": "str", "value": ""}
        return [value_param, min_value_param, max_value_param, label_param]

    @staticmethod
    def get_name():
        return "Progress Bar"

    def update_data(self):
        self.widget.update_progress(
            self.data, self.min_value, self.max_value, self.label
        )

    def on_value_change(self, param, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.value = self.parameters.param("value").value()
        publisher.subscribe(self.value, self.on_data_update)

    def on_min_value_change(self, param, value):
        new = self.parameters.param("min_value").value()
        if new >= self.max_value:
            self.parameters.param("min_value").setValue(self.min_value)
            return
        self.min_value = new
        self.update_data()

    def on_max_value_change(self, param, value):
        new = self.parameters.param("max_value").value()
        if new <= self.min_value:
            self.parameters.param("max_value").setValue(self.max_value)
            return
        self.max_value = new
        self.update_data()

    def on_label_change(self, param, value):
        self.label = self.parameters.param("label").value()
        self.update_data()

    def on_data_update(self, stream, payload):
        time, point = payload
        self.data = float(point)
        self.update_data()

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        super().on_delete()


class ProgressBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = 0
        self.min_value: float = 0
        self.max_value: float = 10.0 # Default max value
        self.label = ""

    def set_parameters(self, min_value, max_value, data, label):
        self.min_value = min_value
        self.max_value = max_value
        self.data = data
        self.label = label

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        width: float = self.width()
        height: float = self.height()
        size: float = min(width/2.5, height) # size of the progress bar

        # Draw the border
        painter.setPen(QColor(255, 255, 255))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        # Calculate the progress width
        progress_width = (
            (self.data - self.min_value)
            / (self.max_value - self.min_value)
            * rect.width()
        )

        # Draw the progress bar with gradient
        gradient = QLinearGradient(0, 0, progress_width, 0)
        gradient.setColorAt(0, QColor(255, 0, 0))
        gradient.setColorAt(1, QColor(255, 200, 0))
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, progress_width, rect.height())

        # Draw the label text with percentage
        percentage = (
            (self.data - self.min_value) / (self.max_value - self.min_value) * 100
        )
        painter.setPen(QColor(0, 0, 0))
        # Change font size according to the size of the progress bar
        font = QFont()
        font.setPointSize(int(size / 3))
        painter.setFont(font)
        if self.label:
            painter.drawText(rect, Qt.AlignCenter, f"{self.label}: {percentage:.1f}%")
        else:
            painter.drawText(rect, Qt.AlignCenter, f"No Label: {percentage:.1f}%")

    def update_progress(self, data, min_value, max_value, label):
        self.set_parameters(min_value, max_value, data, label)
        self.update()

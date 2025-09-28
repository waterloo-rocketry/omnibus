from publisher import publisher
from math import sqrt
from PySide6.QtGui import QLinearGradient, QColor, QBrush
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtGui import QBrush, QFont, QPainter
from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout,QSizePolicy
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter

from .dashboard_item import DashboardItem
from .registry import Register

@Register
class ProgressBarItem(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 10)  # Set the margins of the layout
        self.layout.setSpacing(10)  # Remove the spacing between elements in the layout
        self.resize(200, 100) 
        self.setLayout(self.layout)
        self.vertical_mode = False
        
        self.widget = ProgressBarWidget(self)
        self.label_widget = LabelWidget(self, vertical_mode=False)
        
        # Set size policies
        widget_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        widget_size_policy.setHorizontalStretch(4)  # 4 times larger horizontally
        widget_size_policy.setVerticalStretch(4)    # 4 times larger vertically

        label_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        label_size_policy.setHorizontalStretch(1)   # 1 time (default) horizontally
        label_size_policy.setVerticalStretch(1)   
        
        self.widget.setSizePolicy(widget_size_policy)
        self.label_widget.setSizePolicy(label_size_policy)
        
        self.layout.addWidget(self.widget)
        self.layout.addWidget(self.label_widget)
        
        # Value detection code is based on plot_dash_item.py
        self.parameters.param("value").sigValueChanged.connect(self.on_value_change)

        self.parameters.param("min_value").sigValueChanged.connect(
            self.on_min_value_change
        )
        self.parameters.param("max_value").sigValueChanged.connect(
            self.on_max_value_change
        )
        self.parameters.param("label").sigValueChanged.connect(self.on_label_change)
        self.parameters.param("color").sigValueChanged.connect(self.on_color_change)
        self.parameters.param("vertical").sigValueChanged.connect(self.on_vertical_change)

        self.data: float = 0.0

        self.min_value: float = 0.0
        self.max_value: float = 10.0
        self.label = "No Label Set!"
        self.value = "Not connected"
        self.color = "red"
        
        self.update_data()

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
        color_param = ChecklistParameter(
            name="color",
            type="list",
            value=[],
            limits=["red", "green", "blue", "yellow", "purple", "orange"],
            exclusive=True,
            expanded=False
        )
        vertical_param = {"name": "vertical", "type": "bool", "value": False}
        return [value_param, min_value_param, max_value_param, label_param, color_param, vertical_param]

    @staticmethod
    def get_name():
        return "Progress Bar"

    def update_data(self):
        self.widget.update_progress(
            self.data, self.min_value, self.max_value, self.color
        )
        self.label_widget.update_label(self.label)
        
    def on_vertical_change(self, param, value):
        # Set size policies
        widget_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        widget_size_policy.setHorizontalStretch(4)  # 4 times larger horizontally
        widget_size_policy.setVerticalStretch(4)    # 4 times larger vertically

        label_size_policy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        label_size_policy.setHorizontalStretch(1)   # 1 time (default) horizontally
        label_size_policy.setVerticalStretch(1)   
        
        self.vertical_mode = self.parameters.param("vertical").value()
        self.resize(self.height(), self.width())
        for i in reversed(range(self.layout.count())):
            self.layout.itemAt(i).widget().setParent(None)
        if self.vertical_mode:
            self.widget = VerticalProgressBarWidget(self)
            self.label_widget = LabelWidget(self, vertical_mode=True)
        else:
            self.widget = ProgressBarWidget(self)
            self.label_widget = LabelWidget(self, vertical_mode=False)
        self.widget.setSizePolicy(widget_size_policy)
        self.label_widget.setSizePolicy(label_size_policy)
        self.layout.addWidget(self.widget)
        self.layout.addWidget(self.label_widget)
        self.update_data()

    def on_color_change(self, param, value):
        self.color = self.parameters.param("color").value()
        self.update_data()

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
        
class LabelWidget(QWidget):
    def __init__(self, parent=None, vertical_mode=False):
        super().__init__(parent)
        self.label = "No Label Set!"
        self.vertical_mode = vertical_mode
        
    def set_label(self, label):
        self.label = label

    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        width: int = self.width()
        height: int = self.height()

        # Get minimum scale factor (sqrt(min(width, height)/40))
        if self.vertical_mode:
            scale_factor: float | int = sqrt(min(width, height/2)/40)
        else:
            scale_factor: float | int = sqrt(min(width/2, height)/40)
            
        # Calculate font size based on label length between 0 and 60 characters (decrease as label length increases) 
        font_percent = 1.2 - ((min(len(self.label),60) / 60))
        
        # Set minimum font size to 6, maximum to 23 (based on scale factor)
        font_size = 6 + 17 * font_percent * scale_factor
        
        font = QFont()
        font.setPointSize(font_size)
        painter.setFont(font)
        if self.vertical_mode:
            painter.drawText(rect, Qt.TextWordWrap | Qt.AlignCenter, self.label)
        else:        
            painter.drawText(rect, Qt.TextWordWrap | Qt.AlignCenter, self.label)

    def update_label(self, label):
        self.set_label(label)
        self.update()

class ProgressBarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = 0
        self.connectivity = False
        self.min_value: float = 0
        self.max_value: float = 10.0 # Default max value
        self.color = "red"
        
    def color_to_scalar(self, color: str) -> list[QColor]:
        mapping = {
            "red":      (QColor(255, 0, 0), QColor(255, 200, 0)),
            "green":    (QColor(0, 255, 0), QColor(0, 200, 255)),
            "blue":     (QColor(0, 0, 255), QColor(0, 200, 255)),
            "yellow":   (QColor(255, 255, 0), QColor(255, 200, 0)),
            "purple":   (QColor(128, 0, 128), QColor(128, 200, 128)),
            "orange":   (QColor(255, 165, 0), QColor(255, 200, 0))
        }
        return mapping[color]
    
    def set_color(self, color):
        self.color = color

    def set_parameters(self, min_value, max_value, data, color):
        self.min_value = min_value
        self.max_value = max_value
        self.data = data
        self.color = color
    
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()

        width: int = self.width()
        height: int = self.height()
        size: float | int = min(width/2.5, height) # size of the progress bar

        # Draw the border
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
        color1, color2 = self.color_to_scalar(self.color)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, 0, progress_width, rect.height())

        # Draw the label text with percentage
        percentage = (
            (self.data - self.min_value) / (self.max_value - self.min_value) * 100
        )

        # Change font size according to the size of the progress bar
        font = QFont()
        font.setPointSize(int(size / 1.5))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{percentage:.1f}%")
        
    def update_progress(self, data, min_value, max_value,color):
        self.set_parameters(min_value, max_value, data, color)
        self.update()
        
class VerticalProgressBarWidget(ProgressBarWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        rect = self.rect()
       
        width: int = self.width()
        height: int = self.height()
        size: float | int = min(width/2.5, height) # size of the progress bar
        
        # Draw the border
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)
        
        # Calculate the progress height
        progress_height = (
            (self.data - self.min_value)
            / (self.max_value - self.min_value)
            * rect.height()
        )
        # Draw the progress bar with gradient
        gradient = QLinearGradient(0, rect.height(), 0, rect.height() - progress_height)
        color1, color2 = self.color_to_scalar(self.color)
        gradient.setColorAt(0, color1)
        gradient.setColorAt(1, color2)
        painter.setBrush(QBrush(gradient))
        painter.drawRect(0, rect.height() - progress_height, rect.width(), progress_height)
        
        # Draw the label text with percentage
        percentage = (
            (self.data - self.min_value) / (self.max_value - self.min_value) * 100
        )

        # Change font size according to the size of the progress bar
        font = QFont()
        font.setPointSize(int(size / 1.5))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, f"{percentage:.1f}%")
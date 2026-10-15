from publisher import publisher
from math import sqrt
from typing import TYPE_CHECKING, Any, Callable, Protocol, cast
from PySide6.QtGui import QLinearGradient, QColor
from pyqtgraph.Qt.QtCore import Qt
from pyqtgraph.Qt.QtGui import QBrush, QFont, QPainter, QPaintEvent
from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QWidget, QSizePolicy
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter  # pyright: ignore[reportMissingTypeStubs]

from .dashboard_item import DashboardItem
from .registry import Register

import numbers

if TYPE_CHECKING:
    from dashboard import Dashboard


class _Publisher(Protocol):
    def get_all_streams(self) -> list[str]: ...
    def subscribe(self, stream: str, callback: Callable[[str, Any], None]) -> None: ...
    def unsubscribe_from_all(self, callback: Callable[[str, Any], None]) -> None: ...


_publisher: _Publisher = cast(_Publisher, publisher)


@Register
class ProgressBarItem(DashboardItem):
    main_layout: QVBoxLayout
    vertical_mode: bool
    widget: "ProgressBarWidget"
    label_widget: "LabelWidget"
    data: float
    min_value: float
    max_value: float
    label: str
    value: str
    color: str

    def __init__(self, dashboard: "Dashboard", params: str | None = None) -> None:
        super().__init__(dashboard, params)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(10, 10, 10, 10)  # Set the margins of the layout
        self.main_layout.setSpacing(10)  # Remove the spacing between elements in the layout
        self.resize(200, 100) 
        self.setLayout(self.main_layout)
        self.vertical_mode = False
        
        self.widget = ProgressBarWidget(self)
        self.label_widget = LabelWidget(self, vertical_mode=False)
        
        # Set size policies
        widget_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        widget_size_policy.setHorizontalStretch(4)  # 4 times larger horizontally
        widget_size_policy.setVerticalStretch(4)    # 4 times larger vertically

        label_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        label_size_policy.setHorizontalStretch(1)   # 1 time (default) horizontally
        label_size_policy.setVerticalStretch(1)   
        
        self.widget.setSizePolicy(widget_size_policy)
        self.label_widget.setSizePolicy(label_size_policy)
        
        self.main_layout.addWidget(self.widget)
        self.main_layout.addWidget(self.label_widget)
        
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

        self.data = 0.0

        self.min_value = 0.0
        self.max_value = 10.0
        self.label = "No Label Set!"
        self.value = "Not connected"
        self.color = "red"
        
        self.update_data()

    def add_parameters(self) -> list[Any]:
        value_param = ChecklistParameter(
            name="value",
            type="list",
            value=[],
            limits=_publisher.get_all_streams(),
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
    def get_name() -> str:
        return "Progress Bar"

    def update_data(self) -> None:
        self.widget.update_progress(
            self.data, self.min_value, self.max_value, self.color
        )
        self.label_widget.update_label(self.label)
        
    def on_vertical_change(self, _param: Any, _value: Any) -> None:
        # Set size policies
        widget_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        widget_size_policy.setHorizontalStretch(4)  # 4 times larger horizontally
        widget_size_policy.setVerticalStretch(4)    # 4 times larger vertically

        label_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        label_size_policy.setHorizontalStretch(1)   # 1 time (default) horizontally
        label_size_policy.setVerticalStretch(1)   
        
        self.vertical_mode = self.parameters.param("vertical").value()
        self.resize(self.height(), self.width())
        for i in reversed(range(self.main_layout.count())):
            self.main_layout.itemAt(i).widget().setParent(None)
        if self.vertical_mode:
            self.widget = VerticalProgressBarWidget(self)
            self.label_widget = LabelWidget(self, vertical_mode=True)
        else:
            self.widget = ProgressBarWidget(self)
            self.label_widget = LabelWidget(self, vertical_mode=False)
        self.widget.setSizePolicy(widget_size_policy)
        self.label_widget.setSizePolicy(label_size_policy)
        self.main_layout.addWidget(self.widget)
        self.main_layout.addWidget(self.label_widget)
        self.update_data()

    def on_color_change(self, _param: Any, _value: Any) -> None:
        self.color = self.parameters.param("color").value()
        self.update_data()

    def on_value_change(self, _param: Any, _value: Any) -> None:
        _publisher.unsubscribe_from_all(self.on_data_update)
        self.value = self.parameters.param("value").value()
        _publisher.subscribe(self.value, self.on_data_update)

    def on_min_value_change(self, _param: Any, _value: Any) -> None:
        new = self.parameters.param("min_value").value()
        if new >= self.max_value:
            self.parameters.param("min_value").setValue(self.min_value)
            return
        self.min_value = new
        self.update_data()

    def on_max_value_change(self, _param: Any, _value: Any) -> None:
        new = self.parameters.param("max_value").value()
        if new <= self.min_value:
            self.parameters.param("max_value").setValue(self.max_value)
            return
        self.max_value = new
        self.update_data()

    def on_label_change(self, _param: Any, _value: Any) -> None:
        self.label = self.parameters.param("label").value()
        self.update_data()

    def on_data_update(self, stream: str, payload: Any) -> None:
        _, point = cast("tuple[Any, Any]", payload)
        # Plots can only render numeric values, streams have string data, skip those
        if not isinstance(point, numbers.Real):
            return
        self.data = float(point)
        self.update_data()

    def on_delete(self) -> None:
        _publisher.unsubscribe_from_all(self.on_data_update)
        super().on_delete()
        
class LabelWidget(QWidget):
    label: str
    vertical_mode: bool

    def __init__(self, parent: QWidget | None = None, vertical_mode: bool = False) -> None:
        super().__init__(parent)
        self.label = "No Label Set!"
        self.vertical_mode = vertical_mode
        
    def set_label(self, label: str) -> None:
        self.label = label

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        rect = self.rect()

        width: int = self.width()
        height: int = self.height()

        scale_factor: float | int
        # Get minimum scale factor (sqrt(min(width, height)/40))
        if self.vertical_mode:
            scale_factor = sqrt(min(width, height/2)/40)
        else:
            scale_factor = sqrt(min(width/2, height)/40)
            
        # Calculate font size based on label length between 0 and 60 characters (decrease as label length increases) 
        font_percent = 1.2 - ((min(len(self.label),60) / 60))
        
        # Set minimum font size to 6, maximum to 23 (based on scale factor)
        font_size = 6 + 17 * font_percent * scale_factor
        
        font = QFont()
        font.setPointSize(int(font_size))
        painter.setFont(font)
        if self.vertical_mode:
            painter.drawText(rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.label)
        else:        
            painter.drawText(rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, self.label)

    def update_label(self, label: str) -> None:
        self.set_label(label)
        self.update()

class ProgressBarWidget(QWidget):
    data: float
    connectivity: bool
    min_value: float
    max_value: float
    color: str

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = 0.0
        self.connectivity = False
        self.min_value = 0.0
        self.max_value = 10.0 # Default max value
        self.color = "red"
        
    def color_to_scalar(self, color: str) -> list[QColor]:
        mapping: dict[str, tuple[QColor, QColor]] = {
            "red":      (QColor(255, 0, 0), QColor(255, 200, 0)),
            "green":    (QColor(0, 255, 0), QColor(0, 200, 255)),
            "blue":     (QColor(0, 0, 255), QColor(0, 200, 255)),
            "yellow":   (QColor(255, 255, 0), QColor(255, 200, 0)),
            "purple":   (QColor(128, 0, 128), QColor(128, 200, 128)),
            "orange":   (QColor(255, 165, 0), QColor(255, 200, 0))
        }
        return list(mapping[color])
    
    def set_color(self, color: str) -> None:
        self.color = color

    def set_parameters(self, min_value: float, max_value: float, data: float, color: str) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.data = data
        self.color = color
    
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        rect = self.rect()

        width: int = self.width()
        height: int = self.height()
        size: float | int = min(width/2.5, height) # size of the progress bar

        # Draw the border
        painter.setBrush(Qt.BrushStyle.NoBrush)
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
        painter.drawRect(0, 0, int(progress_width), rect.height())

        # Draw the label text with percentage
        percentage = (
            (self.data - self.min_value) / (self.max_value - self.min_value) * 100
        )

        # Change font size according to the size of the progress bar
        font = QFont()
        font.setPointSize(int(size / 1.5))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{percentage:.1f}%")

    def update_progress(self, data: float, min_value: float, max_value: float,color: str) -> None:
        self.set_parameters(min_value, max_value, data, color)
        self.update()
        
class VerticalProgressBarWidget(ProgressBarWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        rect = self.rect()
       
        width: int = self.width()
        height: int = self.height()
        size: float | int = min(width/2.5, height) # size of the progress bar
        
        # Draw the border
        painter.setBrush(Qt.BrushStyle.NoBrush)
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
        painter.drawRect(0, int(rect.height() - progress_height), rect.width(), int(progress_height))
        
        # Draw the label text with percentage
        percentage = (
            (self.data - self.min_value) / (self.max_value - self.min_value) * 100
        )

        # Change font size according to the size of the progress bar
        font = QFont()
        font.setPointSize(int(size / 1.5))
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{percentage:.1f}%")

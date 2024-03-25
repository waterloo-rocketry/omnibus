from publisher import publisher
from pyqtgraph.Qt.QtCore import Qt, QLineF, QRectF
from pyqtgraph.Qt.QtGui import QBrush, QFont, QPainter, QPainterPath, QPen
from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QWidget
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter, NumericParameterItem

from .dashboard_item import DashboardItem
from .registry import Register

@Register
class GaugeItem(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.widget = GaugeWidget(self)
        self.layout.addWidget(self.widget)

        self.resize(250, 250)

        # Value detection code is based on plot_dash_item.py
        self.parameters.param("value").sigValueChanged.connect(self.on_value_change)
        
        self.parameters.param("min_value").sigValueChanged.connect(self.on_min_value_change)
        self.parameters.param("max_value").sigValueChanged.connect(self.on_max_value_change)
        self.parameters.param("step_value").sigValueChanged.connect(self.on_step_value_change)
        self.parameters.param("tick_count").sigValueChanged.connect(self.on_tick_count_change)

        self.data: float = 0.0

        self.min_value: int = 0
        self.max_value: int = 10
        self.step_value: int = 1
        self.tick_count: int = 5

        self.value = "Not connected"

    def add_parameters(self):
        value_param = ChecklistParameter(name="value",
                                          type="list",
                                          value=[],
                                          limits=publisher.get_all_streams(),
                                          exclusive=True)
        min_value_param = {"name": "min_value", "type": "int", "value": 0}
        max_value_param = {"name": "max_value", "type": "int", "value": 10}
        step_value_param = {"name": "step_value", "type": "int", "value": 1}
        tick_count_param = {"name": "tick_count", "type": "int", "value": 5}
        return [value_param, min_value_param, max_value_param, step_value_param, tick_count_param]

    @staticmethod
    def get_name():
        return "Gauge"
    
    def on_value_change(self, param, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.value = self.parameters.param('value').value()
        publisher.subscribe(self.value, self.on_data_update)

    def on_min_value_change(self, param, value):
        self.min_value = self.parameters.param("min_value").value()
        self.widget.update()

    def on_max_value_change(self, param, value):
        self.max_value = self.parameters.param("max_value").value()
        self.widget.update()

    def on_step_value_change(self, param, value):
        self.step_value = self.parameters.param("step_value").value()
        self.widget.update()

    def on_tick_count_change(self, param, value):
        self.tick_count = self.parameters.param("tick_count").value()
        self.widget.update()
    
    def on_data_update(self, stream, payload):
        time, point = payload
        self.data = float(point)
        self.widget.update()
    
class GaugeWidget(QWidget):
    def __init__(self, item: GaugeItem):
        super().__init__()
        self.item = item

    def paintEvent(self, paintEvent):
        width = self.width()
        height = self.height()
        with QPainter(self) as painter:
            # Draw circle
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            side = min(width, height) - 30
            left = (width - side) / 2
            top = (height - side) / 2
            painter.drawEllipse(QRectF(left, top, side, side))

            # Tick marks and text

            radius = side / 2
            cx = left + radius
            cy = top + radius
            tick_length = 10

            # Angle clockwise with 0 at the top
            start_angle = -120.0
            end_angle = 120.0
            tick_length = 10
            step_length = 15
            min_value = self.item.min_value
            max_value = self.item.max_value
            step_value = self.item.step_value
            tick_count = self.item.tick_count

            # Invalid conditions
            if max_value < min_value:
                return

            # rotate about the center
            painter.save()
            painter.translate(cx, cy)

            if step_value > 0:
                step = min_value
                while step <= max_value:
                    angle = (step - min_value) / (max_value - min_value) * (end_angle - start_angle) + start_angle
                    painter.save()
                    painter.rotate(angle)
                    painter.drawLine(QLineF(0, -(radius - step_length), 0, -radius))
                    painter.drawText(-15, -(radius - step_length), 30, 20, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, str(step))
                    for tick in range(1, tick_count + 1):
                        # avoid floating point comparison
                        if (step * tick_count + step_value * tick) > max_value * tick_count:
                            break
                        angle = (step_value / tick_count * tick) / (max_value - min_value) * (end_angle - start_angle)
                        painter.save()
                        painter.rotate(angle)
                        painter.drawLine(QLineF(0, -(radius - tick_length), 0, -radius))
                        painter.restore()
                    step += step_value
                    painter.restore()


            value = self.item.data
            # Value is clamped to the bounds
            angle = max(min((value - min_value) / (max_value - min_value), 1.05), -0.05) * (end_angle - start_angle) + start_angle
            painter.save()
            painter.rotate(angle)
            path = QPainterPath()
            path.moveTo(5, 0)
            path.arcTo(-5, -5, 10, 10, 0, -180)
            path.lineTo(0, -radius + 5)
            path.lineTo(5, 0)
            painter.fillPath(path, QBrush(Qt.GlobalColor.red))
            painter.restore()

            painter.restore()

            painter.drawText(cx - 15, top + side * 0.8 - 20, 30, 20, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, str(value))

            font = QFont()
            font.setPointSize(6)

            painter.setFont(font)
            painter.drawText(0, height - 10, width, 10, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, self.item.value)
            
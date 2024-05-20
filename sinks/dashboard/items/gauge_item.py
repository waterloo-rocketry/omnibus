from publisher import publisher
from pyqtgraph.Qt.QtCore import Qt, QLineF, QRectF
from pyqtgraph.Qt.QtGui import QBrush, QFont, QPainter, QPainterPath
from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QWidget
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter

from .dashboard_item import DashboardItem
from .registry import Register

from decimal import Decimal

@Register
class GaugeItem(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.widget = GaugeWidget(self)
        self.layout.addWidget(self.widget)

        self.resize(200, 250)

        # Value detection code is based on plot_dash_item.py
        self.parameters.param("value").sigValueChanged.connect(self.on_value_change)
        
        self.parameters.param("min_value").sigValueChanged.connect(self.on_min_value_change)
        self.parameters.param("max_value").sigValueChanged.connect(self.on_max_value_change)
        self.parameters.param("label").sigValueChanged.connect(self.on_label_change)

        self.data: float = 0.0

        self.min_value: float = 0.0
        self.max_value: float = 10.0
        self.label = ""

        self.value = "Not connected"

    def add_parameters(self):
        value_param = ChecklistParameter(name="value",
                                          type="list",
                                          value=[],
                                          limits=publisher.get_all_streams(),
                                          exclusive=True)
        min_value_param = {"name": "min_value", "type": "float", "value": 0.0}
        max_value_param = {"name": "max_value", "type": "float", "value": 10.0}
        label_param = {"name": "label", "type": "str", "value": ""}
        return [value_param, min_value_param, max_value_param, label_param]

    @staticmethod
    def get_name():
        return "Gauge"
    
    def on_value_change(self, param, value):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.value = self.parameters.param('value').value()
        publisher.subscribe(self.value, self.on_data_update)

    def on_min_value_change(self, param, value):
        new = self.parameters.param("min_value").value()
        if new >= self.max_value:
            self.parameters.param("min_value").setValue(self.min_value)
            return
        self.min_value = new
        self.widget.update()

    def on_max_value_change(self, param, value):
        new = self.parameters.param("max_value").value()
        if new <= self.min_value:
            self.parameters.param("max_value").setValue(self.max_value)
            return
        self.max_value = new
        self.widget.update()

    def on_label_change(self, param, value):
        self.label = self.parameters.param("label").value()
        self.widget.update()
    
    def on_data_update(self, stream, payload):
        time, point = payload
        self.data = float(point)
        self.widget.update()

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        super().on_delete()
    
class GaugeWidget(QWidget):
    def __init__(self, item: GaugeItem):
        super().__init__()
        self.item = item

    def paintEvent(self, paintEvent):
        width = self.width()
        height = self.height()
        if width < 100 or height < 100:
            return
        with QPainter(self) as painter:
            # Draw circle
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            side = min(width, height * 0.9)
            left = (width - side) / 2
            top = (height - side) / 2 - side / 20
            painter.drawEllipse(QRectF(left, top, side, side))

            # Tick marks and text
            radius = side / 2
            cx = left + radius
            cy = top + radius
            tick_length = 10

            # Angle clockwise with 0 at the top
            start_angle = -120.0
            end_angle = 120.0
            tick_length = 4
            step_length = 8
            min_value: float = self.item.min_value
            max_value: float = self.item.max_value
            min_value_decimal = Decimal("{0:.6g}".format(min_value))
            max_value_decimal = Decimal("{0:.6g}".format(max_value))

            # Invalid conditions
            if max_value_decimal <= min_value_decimal:
                return

            value_range = max_value_decimal - min_value_decimal
            exp = value_range.adjusted()
            power = Decimal(10) ** exp
            coeff = value_range / power
            # Keep at least 5 steps but space them out
            if coeff >= 8:
                step_value = 2 * power
            elif coeff >= 4:
                step_value = power
            elif coeff >= 2:
                step_value = power / 2
            else:
                step_value = power / 5
            tick_count = 5

            # rotate about the center
            painter.save()
            painter.translate(cx, cy)
            painter.setPen(Qt.GlobalColor.black)
            
            font = QFont()
            font.setPointSize(side / 14)
            painter.setFont(font)

            step = min_value_decimal
            while step <= max_value_decimal:
                angle = (float(step) - min_value) / (max_value - min_value) * (end_angle - start_angle) + start_angle
                painter.save()
                painter.rotate(angle)
                painter.drawLine(QLineF(0, -(radius - step_length), 0, -radius))
                step_display_number = int(step) if step == int(step) else step
                step_str = str(step_display_number)
                painter.drawText(-side * 0.15, -(radius - step_length), side * 0.3, side * 0.2, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, step_str)
                for tick in range(1, tick_count + 1):
                    if (step + step_value * tick / tick_count) > max_value_decimal:
                        break
                    angle = (float(step_value) / tick_count * tick) / (max_value - min_value) * (end_angle - start_angle)
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
            path.moveTo(3, 0)
            path.arcTo(-3, -3, 6, 6, 0, -180)
            path.lineTo(0, -radius + 3)
            path.lineTo(3, 0)
            painter.fillPath(path, QBrush(Qt.GlobalColor.red))
            painter.restore()

            painter.restore()

            painter.save()
            painter.setPen(Qt.GlobalColor.black)

            font = QFont()
            font.setPointSize(side / 10)
            painter.setFont(font)
            value_text = "{0:.6g}".format(value)
            painter.drawText(cx - side * 0.3, top + side * 0.8 - side / 10, side * 0.6, side / 5, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, value_text)

            painter.restore()

            label = self.item.label if self.item.label != "" else self.item.value

            font = QFont()
            font.setPointSize(side / 14)
            painter.setFont(font)
            painter.drawText(0, height - side / 8, width, side / 8, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, label)

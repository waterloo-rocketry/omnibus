from pyqtgraph.Qt.QtCore import Qt, QLineF, QRectF
from pyqtgraph.Qt.QtGui import QPainter, QBrush
from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QCheckBox, QWidget

from .dashboard_item import DashboardItem
from .registry import Register

@Register
class GaugeItem(DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)
        
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        
        self.widget = GaugeWidget()
        self.layout.addWidget(self.widget)

        self.resize(250, 250)

    @staticmethod
    def get_name():
        return "Gauge"
    
class GaugeWidget(QWidget):
    def paintEvent(self, paintEvent):
        rect = paintEvent.rect()
        with QPainter(self) as painter:
            # Draw circle
            painter.setBrush(QBrush(Qt.GlobalColor.white))
            side = min(rect.width(), rect.height()) - 1
            left = (rect.width() - side) / 2
            top = (rect.height() - side) / 2
            painter.drawEllipse(QRectF(left, top, side, side))

            # Tick marks and text

            radius = side // 2
            cx = left + radius
            cy = top + radius
            tick_length = 10
            # Angle increment clockwise
            step_angle = 30.0
            # Number of ticks
            tick_count = 8
            # Initial angle clockwise from the top
            init_angle = -(tick_count - 1) * step_angle / 2

            painter.save()
            painter.translate(cx, cy)
            painter.rotate(init_angle)
            for i in range(tick_count):
                painter.drawLine(QLineF(0, -(radius - tick_length), 0, -radius))
                painter.drawText(-10, -(radius - tick_length), 20, 20, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, str(i))
                painter.rotate(step_angle)

            painter.restore()


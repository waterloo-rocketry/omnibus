from publisher import publisher
from pyqtgraph.Qt.QtWidgets import QBoxLayout
from pyqtgraph.parametertree.parameterTypes import ListParameter
import pyqtgraph.opengl as gl
from sinks.dashboard.items.dashboard_item import DashboardItem
from .registry import Register


@Register
class Position3DDashItem (DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        # Specify the layout
        self.layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.setLayout(self.layout)

        self.series = self.parameters.param('series').value()

        # initilize 3D environment
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=40)
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 0)
        self.view.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 0)
        self.view.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, -10)
        self.view.addItem(gz)

        publisher.subscribe(self.series, self.on_data_update_position)
        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.pos_list = []
        self.line = None

        # need to set minimum dimensions because it
        # defaults to 40 for some reason
        self.resize(600, 600)

        # add it to the layout
        self.layout.addWidget(self.view)

    def add_parameters(self):
        series_param = ListParameter(name='series',
                                          type='list',
                                          default="",
                                          limits=publisher.get_all_streams())
        return [series_param]

    def on_series_change(self, param, value):
        publisher.unsubscribe_from_all(self.on_data_update_position)
        self.series = value
        publisher.subscribe(self.series, self.on_data_update_position)

    def on_data_update_position(self, stream, payload):
        time, point = payload

        # Ensuring point is of the right format.
        match point:
            case x, y, z:
                pass
            case _:
                return None

        self.pos_list.append(tuple(point))
        if len(self.pos_list) < 2:
            return None

        if self.line is None:
            self.line = gl.GLLinePlotItem(pos=self.pos_list)
            self.view.addItem(self.line)
            return None

        if len(self.pos_list) > 200:
            self.pos_list.pop(0)

        self.line.setData(pos=self.pos_list, color=(1.0, 1.0, 1.0, 1.0))

    @staticmethod
    def get_name():
        return "3D Position Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update_position)

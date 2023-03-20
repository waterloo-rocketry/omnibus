from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph.opengl as gl
from sinks.dashboard.items.dashboard_item import DashboardItem
from utils import prompt_user
from .registry import Register


@Register
class Position3DDashItem (DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # save props as a field
        self.props = props

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

        publisher.subscribe(self.props, self.on_data_update_position)
        self.pos_list = []
        self.line = gl.GLLinePlotItem(pos=self.pos_list)
        self.view.addItem(self.line)

        # add it to the layout
        self.layout.addWidget(self.view, 0, 0)

    def prompt_for_properties(self):

        series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            publisher.get_all_streams(),
        )
        if not series:
            return None

        return series

    def on_data_update_position(self, stream, payload):
        time, point = payload
        self.pos_list.append(tuple(point))
        if len(self.pos_list) > 200:
            self.pos_list.pop(0)

        self.line.setData(pos=self.pos_list, color=(1.0, 1.0, 1.0, 1.0))

    def get_props(self):
        return self.props

    def get_name():
        return "3D Position Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update_position)

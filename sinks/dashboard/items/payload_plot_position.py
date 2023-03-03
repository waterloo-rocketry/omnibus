from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget
import pyqtgraph.opengl as gl
from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from sinks.dashboard.items.dashboard_item import DashboardItem
import config
from utils import prompt_user
import time

from .registry import Register


@Register
class PayloadDashItem (DashboardItem):
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

        publisher.subscribe(self.props[0], self.on_data_update_position)
        self.pos_list = []
        self.line = gl.GLLinePlotItem()
        self.view.addItem(self.line)

        # add it to the layout
        self.layout.addWidget(self.view, 0, 0)
        self.start_time = time.time()

    def prompt_for_properties(self):

        orientation_mode = prompt_user(
            self,
            "Orientation Mode",
            "Is the data a position?",
            "items",
            ["Position"]
        )

        enable_orientation = False

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None

        return [channel_and_series, enable_orientation]

    def on_data_update_position(self, stream, payload):
        time, point = payload
        self.pos_list.append(tuple(point))
        if len(self.pos_list) > 200:
            self.pos_list.pop(0)

        self.line.setData(pos=self.pos_list, color=(1.0, 1.0, 1.0, 1.0))

    def get_props(self):
        return self.props

    def get_name():
        return "Payload Position Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update_position)

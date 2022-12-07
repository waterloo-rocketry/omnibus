from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget


from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from sinks.dashboard.items.dashboard_item import DashboardItem
import config
from utils import prompt_user


class PlotDashItem (DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = 0
        self.times = np.zeros(self.size)
        self.points = np.zeros(self.size)
        self.sum = 0  # sum of stream
        # "size" of running average
        self.avgSize = config.RUNNING_AVG_DURATION * config.GRAPH_RESOLUTION
        self.time_offset = 0

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # set the limit for triggering red tint area
        self.limit = props[1]

        # save props as a field
        self.props = props

        # subscribe to stream dictated by properties
        publisher.subscribe(self.props[0], self.on_data_update)

        # create the plot
        self.plot = pg.PlotItem(title=self.props[0], left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()

        self.curve = self.plot.plot(self.times, self.points, pen='y')
        if self.limit is not None:
            self.warning_line = self.plot.plot([], [], brush=(255, 0, 0, 50), pen='r')

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def prompt_for_properties(self):

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None

        # threshold_input == None if not set
        threshold_input = prompt_user(
            self,
            "Threshold Value",
            "Set an upper limit",
            "number",
            cancelText="No Threshold"
        )

        props = [channel_and_series, threshold_input]

        return props

    def on_data_update(self, payload):
        time, point = payload
        desc = payload[2] if (len(payload) > 2) else ""

        time += self.time_offset

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last == 0:  # is this the first point we're plotting?
            self.times.fill(time)  # prevent a rogue datapoint at (0, 0)
            self.points.fill(point)
            self.sum = self.avgSize * point

        self.last += 1 / config.GRAPH_RESOLUTION

        self.sum -= self.points[self.size - self.avgSize]
        self.sum += point

        # add the new datapoint to the end of each array, shuffle everything else back
        self.times[:-1] = self.times[1:]
        self.times[-1] = time
        self.points[:-1] = self.points[1:]
        self.points[-1] = point

        min_point = min(self.points)
        max_point = max(self.points)

        # set the displayed range of Y axis
        self.plot.setYRange(min_point, max_point, padding=0.1)

        if self.limit is not None:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData([self.times[0], self.times[-1]], [self.limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)

        # plot the data curve
        self.curve.setData(self.times, self.points)

        # current value readout in the title
        self.plot.setTitle(
            f"[{sum(self.points)/len(self.points): <4.4f}] [{self.points[-1]: <4.4f}] {self.props[0]}")

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

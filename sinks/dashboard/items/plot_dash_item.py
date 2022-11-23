from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QGridLayout

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from sinks.dashboard.items.dashboard_item import DashboardItem
from sinks.dashboard.items.subscriber import Subscriber
import config
from utils import prompt_user


class PlotDashItem (DashboardItem, Subscriber):
    def __init__(self, props=None):
        # Call this in **every** dash item constructor
        DashboardItem.__init__(self)
        Subscriber.__init__(self)

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = 0
        self.times = np.zeros(self.size)
        self.points = np.zeros(self.size)
        self.sum = 0  # sum of series
        # "size" of running average
        self.avgSize = config.RUNNING_AVG_DURATION * config.GRAPH_RESOLUTION
        self.time_offset = 0

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # store the properties
        self.props = props

        # if no properties are passed in
        # prompt the user for them
        if self.props == None:
            items = list(publisher.get_DAQ_series())

            self.props = prompt_user(
                self,
                "Data Series",
                "The series you wish to plot",
                "items",
                items
            )

        # subscribe to series dictated by properties
        self.subscribe_to(self.props)

        # create the plot
        self.plot = pg.PlotItem(title=self.props, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(self.times, self.points, pen='y')

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def on_data_update(self, payload):
        # Migration of Series logic on add

        time = payload[0]
        point = payload[1]
        desc = ""

        if (len(payload) > 2):
            desc = payload[2]

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

        # update the displayed data

        # find the time range
        t = round(self.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        min_time = t - config.GRAPH_DURATION + config.GRAPH_STEP
        max_time = t + config.GRAPH_STEP

        # filter the times

        times = [self.times[i] for i in range(self.size) if (
            self.times[i] >= min_time and self.times[i] <= max_time)]

        points = [self.points[i] for i in range(self.size) if (
            self.times[i] >= min_time and self.times[i] <= max_time)]

        self.curve.setData(times, points)

        # current value readout in the title
        self.plot.setTitle(
                f"[{sum(points)/len(points): <4.4f}] [{self.points[-1]: <4.4f}] {self.props} {desc}")

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

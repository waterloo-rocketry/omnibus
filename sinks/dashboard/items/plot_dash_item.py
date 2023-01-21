from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget


from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from .dashboard_item import DashboardItem
import config
from utils import prompt_user
from .registry import Register


@Register
class PlotDashItem(DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = {}

        # storing the series name as key, its time and points as value
        # since each PlotDashItem can contain more than one curve
        self.times = {}
        self.points = {}

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # set the limit for triggering red tint area
        self.limit = props[1]

        # save props as a field
        self.props = props
        # a list of series names to be plotted
        self.series = self.props[0]

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # a default color list for plotting multiple curves
        # yellow green cyan white blue magenta
        self.color = ['y', 'g', 'c', 'w', 'b', 'm']

        # create the plot
        self.plot = pg.PlotItem(title='/'.join(self.series), left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        if (len(self.series) > 1):
            self.plot.addLegend()
        # draw the curves
        # storing the series name as key, its plot object as value
        # update all curves every time on_data_update() is called
        self.curves = {}
        for i,series in enumerate(self.series):
            curve = self.plot.plot([], [], pen=self.color[i], name=series)
            self.curves[series] = curve
            self.times[series] = np.zeros(self.size)
            self.points[series] = np.zeros(self.size)
            self.last[series] = 0

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
            "Select up to 6 series you wish to plot",
            "checkbox",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None
        # if more than 6 series are selected, only plot the first 6
        if len(channel_and_series) > 6:
            channel_and_series = channel_and_series[:6]

        threshold_input = prompt_user(
            self,
            "Threshold Value",
            "Set an upper limit for " + '/'.join(channel_and_series),
            "number",
            cancelText="No Threshold"
        )
        props = [channel_and_series, threshold_input]

        return props

    def on_data_update(self, stream, payload):
        time, point = payload
        desc = payload[2] if (len(payload) > 2) else ""

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last[stream] < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last[stream] == 0:  # is this the first point we're plotting?
            # prevent a rogue datapoint at (0, 0)
            self.times[stream].fill(time)
            self.points[stream].fill(point)

        self.last[stream] += 1 / config.GRAPH_RESOLUTION

        # add the new datapoint to the end of the corresponding stream array, shuffle everything else back
        self.times[stream][:-1] = self.times[stream][1:]
        self.times[stream][-1] = time
        self.points[stream][:-1] = self.points[stream][1:]
        self.points[stream][-1] = point

        # get the min/max point in the whole data set
        min_point = min([min(v) for v in self.points.values()])
        max_point = max([max(v) for v in self.points.values()])

        # set the displayed range of Y axis
        self.plot.setYRange(min_point, max_point, padding=0.1)

        if self.limit is not None:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData(
                [self.times[stream][0], self.times[stream][-1]], [self.limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)

        # update the data curve
        self.curves[stream].setData(self.times[stream], self.points[stream])

        # value readout in the title
        # avg values
        avg_values = [sum(item)/len(item) for item in self.points.values()]
        title = "avg: "
        for v in avg_values:
            title += f"[{v: < 4.4f}]"
        # current values
        title += "    current: "
        last_values = [item[-1] for item in self.points.values()]
        for v in last_values:
            title += f"[{v: < 4.4f}]"
        # data series name
        title += "    " + "/".join(self.series)

        self.plot.setTitle(title)

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

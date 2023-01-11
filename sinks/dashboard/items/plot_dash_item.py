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
        self.last = 0
        self.times = {}
        self.points = {}
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
        self.series = self.props[0]

        self.curve_count = 0
        self.curve_num = len(self.series)

        # subscribe to stream dictated by properties
        for i in range(self.curve_num):
            publisher.subscribe(self.series[i], self.on_data_update)

        self.color = ['w', 'g', 'b', 'm', 'y', 'c']
        # create the plot
        self.plot = pg.PlotItem(title='/'.join(self.series), left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curves = {}
        for i in range(self.curve_num):
            curve = self.plot.plot([], [], pen=self.color[i])
            self.curves[self.series[i]] = curve
            self.times[self.series[i]] = np.zeros(self.size)
            self.points[self.series[i]] = np.zeros(self.size)

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
            "The serie(s) you wish to plot",
            "checkbox",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None

        # if plotting separately, prompt user for separate thresholds
        if channel_and_series[1]:
            threshold_inputs = []
            for item in channel_and_series[0]:
                msg = "Set an upper limit for " + item
                # threshold_input == None if not set
                threshold_input = prompt_user(
                    self,
                    "Threshold Value",
                    msg,
                    "number",
                    cancelText="No Threshold"
                )
                threshold_inputs.append(threshold_input)
            props = [channel_and_series, threshold_inputs]
        # if plotting in the same plot
        else:
            threshold_input = prompt_user(
                self,
                "Threshold Value",
                "Set an upper limit for " + '/'.join(channel_and_series[0]),
                "number",
                cancelText="No Threshold"
            )
            props = [channel_and_series, threshold_input]

        return props

    def on_data_update(self, stream, payload):
        time, point = payload
        desc = payload[2] if (len(payload) > 2) else ""

        time += self.time_offset

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last == 0:  # is this the first point we're plotting?
            # prevent a rogue datapoint at (0, 0)
            for v in self.times.values():
                v.fill(time)
            for v in self.points.values():
                v.fill(point)
            self.sum = self.avgSize * point

        self.last += 1 / config.GRAPH_RESOLUTION

        self.sum -= self.points[stream][self.size - self.avgSize]
        self.sum += point

        # add the new datapoint to the end of each array, shuffle everything else back
        self.times[stream][:-1] = self.times[stream][1:]
        self.times[stream][-1] = time
        self.points[stream][:-1] = self.points[stream][1:]
        self.points[stream][-1] = point

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
        # plot the data curves
        for k, v in self.curves.items():
            v.setData(self.times[k], self.points[k])

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

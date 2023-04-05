from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout, QMenu
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter
from pyqtgraph.Qt.QtCore import QEvent
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget


from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from .dashboard_item import DashboardItem
import config
from .registry import Register
from utils import prompt_user


@Register
class PlotDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        self.length = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.avgSize = config.GRAPH_RESOLUTION * config.RUNNING_AVG_DURATION
        self.sum = {}
        self.last = {}

        # storing the series name as key, its time and points as value
        # since each PlotDashItem can contain more than one curve
        self.times = {}
        self.points = {}

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)

        self.series = self.parameters.param('series').value()

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # a default color list for plotting multiple curves
        # yellow green cyan white blue magenta
        self.color = ['y', 'g', 'c', 'w', 'b', 'm']

        # create the plot
        self.plot = self.create_plot()

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def addParameters(self):
        series_param = ChecklistParameter(name='series',
                                          type='list',
                                          value=[],
                                          limits=publisher.get_all_streams())
        limit_param = {'name': 'limit', 'type': 'float', 'value': 0}
        return [series_param, limit_param]

    def on_series_change(self, param, value):
        if len(value) > 6:
            self.parameters.param('series').setValue(value[:6])
        self.series = self.parameters.param('series').childrenValue()
        # resubscribe to the new streams
        publisher.unsubscribe_from_all(self.on_data_update)
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)
        # recreate the plot with new series and add it to the layout
        self.plot = self.create_plot()
        self.widget = pg.PlotWidget(plotItem=self.plot)
        self.layout.addWidget(self.widget, 0, 0)

    # Create the plot item
    def create_plot(self):
        plot = pg.PlotItem(title='/'.join(self.series), left="Data", bottom="Seconds")
        plot.setMenuEnabled(False)     # hide the default context menu when right-clicked
        plot.setMouseEnabled(x=False, y=False)
        plot.hideButtons()
        if (len(self.series) > 1):
            plot.addLegend()
        # draw the curves
        # storing the series name as key, its plot object as value
        # update all curves every time on_data_update() is called
        self.curves = {}
        for i, series in enumerate(self.series):
            curve = plot.plot([], [], pen=self.color[i], name=series)
            self.curves[series] = curve
            self.times[series] = np.zeros(self.length)
            self.points[series] = np.zeros(self.length)
            self.sum[series] = 0
            self.last[series] = 0

        # initialize the threshold line, but do not plot it unless a limit is specified
        self.warning_line = plot.plot([], [], brush=(255, 0, 0, 50), pen='r')

        return plot

    def prompt_for_parameters(self):
        channel_and_series = prompt_user(
            self,
            "Data series",
            "Select the series you wish to plot. Up to 6 if plotting together.",
            "checkbox",
            publisher.get_all_streams(),
        )
        if not channel_and_series[0]:
            return None
        # if more than 6 series are selected, only plot the first 6
        if len(channel_and_series) > 6:
            channel_and_series = channel_and_series[:6]

        if channel_and_series[1]:     # plot separately
            params = [{"series": [series], "limit": 0} for series in channel_and_series[0]]
        else:                           # plot together
            # if more than 6 series are selected, only plot the first 6
            if len(channel_and_series) > 6:
                channel_and_series = channel_and_series[:6]
            params = [{"series": channel_and_series[0], "limit": 0}]

        return params

    def on_data_update(self, stream, payload):
        time, point = payload

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last[stream] < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last[stream] == 0:  # is this the first point we're plotting?
            # prevent a rogue datapoint at (0, 0)
            self.times[stream].fill(time)
            self.points[stream].fill(point)
            self.sum[stream] = self.avgSize * point

        self.last[stream] = time

        self.sum[stream] -= self.points[stream][self.length - self.avgSize]
        self.sum[stream] += point

        # add the new datapoint to the end of the corresponding stream array, shuffle everything else back
        self.times[stream][:-1] = self.times[stream][1:]
        self.times[stream][-1] = time
        self.points[stream][:-1] = self.points[stream][1:]
        self.points[stream][-1] = point

        # get the min/max point in the whole data set
        min_point = min(min(v) for v in self.points.values())
        max_point = max(max(v) for v in self.points.values())

        # set the displayed range of Y axis
        self.plot.setYRange(min_point, max_point, padding=0.1)

        limit = self.parameters.param('limit').value()
        if limit != 0:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData(
                [self.times[stream][0], self.times[stream][-1]], [limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)
        else:
            self.warning_line.setData([], [])
            self.warning_line.setFillLevel(0)

        # update the data curve
        self.curves[stream].setData(self.times[stream], self.points[stream])

        # round the time to the nearest GRAPH_STEP
        t = round(self.times[stream][-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        self.plot.setXRange(t - config.GRAPH_DURATION + config.GRAPH_STEP,
                            t + config.GRAPH_STEP, padding=0)

        # value readout in the title for at most 2 series
        title = ""
        if len(self.series) <= 2:
            # avg values
            avg_values = [self.sum[item]/self.avgSize for item in self.series]
            title += "avg: "
            for v in avg_values:
                title += f"[{v: < 4.4f}]"
            # current values
            title += "    current: "
            last_values = [self.points[item][-1] for item in self.series]
            for v in last_values:
                title += f"[{v: < 4.4f}]"
            title += "    "
        # data series name
        title += "/".join(self.series)

        self.plot.setTitle(title)

    @staticmethod
    def get_name():
        return "Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

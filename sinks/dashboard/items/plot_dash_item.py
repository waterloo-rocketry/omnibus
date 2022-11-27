from parsers import Parser
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QGridLayout

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from sinks.dashboard.items.dashboard_item import DashboardItem
import config
from utils import prompt_user


class PlotDashItem (DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # subscribe to series dictated by properties
        self.series = Parser.get_series(props[0], props[1])
        self.subscribe_to_series(self.series)

        # set the limit for triggering red tint area
        self.limit = props[2]

        # save props as a field
        self.props = props

        # create the plot
        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        # create data curve and warning line
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')
        if self.limit is not None:
            self.warning_line = self.plot.plot([], [], brush=(255, 0, 0, 50), pen='r')

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def prompt_for_properties(self):
        items = []
        for channel in Parser.parsers.keys():
            all_series = [series.name for series in Parser.get_all_series(channel)]
            all_series.sort()
            for series in all_series:
                items.append(f"{channel}|{series}")

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            items,
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

        props = channel_and_series.split("|")
        props.append(threshold_input)

        return props

    def on_data_update(self, series):
        # update the displayed data

        # find the time range
        t = round(series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        min_time = t - config.GRAPH_DURATION + config.GRAPH_STEP
        max_time = t + config.GRAPH_STEP

        # filter the times, points
        times = [series.times[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]
        points = [series.points[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]

        min_point = min(points)
        max_point = max(points)

        # set the displayed range of Y axis
        self.plot.setYRange(min_point, max_point, padding=0.1)

        if self.limit is not None:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData([times[0], times[-1]], [self.limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)

        # plot the data curve
        self.curve.setData(times, points)

        # current value readout in the title
        self.plot.setTitle(
            f"[{sum(points)/len(points): <4.4f}] [{points[-1]}] {series.name} {series.desc and (series.desc + ' ') or ''}")

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

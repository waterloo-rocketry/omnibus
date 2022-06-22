from parsers import Parser
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QGridLayout

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from dashboarditem import DashboardItem
import config


class PlotDashItem (DashboardItem):
    def __init__(self, props=None):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # store the properties
        self.props = props

        # if no properties are passed in
        # prompt the user for them
        if self.props == None:
            items = []
            for channel in Parser.parsers.keys():
                all_series = [series.name for series in Parser.get_all_series(channel)]
                all_series.sort()
                for series in all_series:
                    items.append(f"{channel}|{series}")

            channel_and_series = self.prompt_user(
                "Data Series", "The series you wish to plot", "items", items)
            self.props = channel_and_series.split("|")

        # subscribe to series dictated by properties
        self.series = Parser.get_series(self.props[0], self.props[1])
        self.subscribe_to_series(self.series)

        # create the plot
        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def on_data_update(self, series):
        # update the displayed data
        self.curve.setData(series.times, series.points)

        # current value readout in the title
        self.plot.setTitle(
            f"[{series.get_running_avg(): <4.4f}] [{series.points[-1]}] {series.name} {series.desc and (series.desc + ' ') or ''}")

        # round the time to the nearest GRAPH_STEP
        t = round(series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        min_time = t - config.GRAPH_DURATION + config.GRAPH_STEP
        max_time = t + config.GRAPH_STEP

        self.plot.setXRange(min_time, max_time, padding=0)

        max_data = max([series.points[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)])
        min_data = min([series.points[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)])

        pad = (max_data - min_data) * 0.1
        max_data += pad
        min_data -= pad

        self.plot.setYRange(min_data, max_data, padding=0)

    def get_props(self):
        return self.props

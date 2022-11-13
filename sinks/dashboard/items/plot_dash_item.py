from parsers import temp_series_dict
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
            items = [sensor for sensor, series in temp_series_dict.items()]

            self.props = prompt_user(
                self,
                "Data Series",
                "The series you wish to plot",
                "items",
                items
                )

        # subscribe to series dictated by properties
        self.series = temp_series_dict[self.props]
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

        # find the time range
        t = round(series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        min_time = t - config.GRAPH_DURATION + config.GRAPH_STEP
        max_time = t + config.GRAPH_STEP

        #filter the times

        times = [series.times[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]

        points = [series.points[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]

        self.curve.setData(times, points)

        # current value readout in the title
        self.plot.setTitle(
            f"[{sum(points)/len(points): <4.4f}] [{series.points[-1]}] {series.name} {series.desc and (series.desc + ' ') or ''}")

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

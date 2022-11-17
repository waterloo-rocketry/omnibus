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

            channel_and_series = prompt_user(
                self,
                "Data Series",
                "The series you wish to plot",
                "items",
                items,
            )
            if not channel_and_series:
                raise Exception
            
            threshold_input = prompt_user(
                self,
                "Threshold Value",
                "Set an upper limit",
                "number"
            )
            if threshold_input == None:
                raise Exception

            self.props = channel_and_series.split("|")
            self.props.append(threshold_input)

        # subscribe to series dictated by properties
        self.series = Parser.get_series(self.props[0], self.props[1])
        self.subscribe_to_series(self.series)

        # set the limit for triggering red tint area
        self.limit = self.props[2]

        # create the plot
        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        # create data curve and warning line
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')
        self.warning_line = self.plot.plot([], [], fillLevel=self.limit*10, brush=(255,0,0,50),pen='r')

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

        # filter the times, points
        times = [series.times[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]
        points = [series.points[i] for i in range(series.size) if (
            series.times[i] >= min_time and series.times[i] <= max_time)]
        
        min_point = min(points)
        max_point = max(points)
        
        #set the displayed range of Y axis
        self.plot.setYRange(min_point,max_point,padding=0.1)

        # plot the warning line
        self.warning_line.setData(times,[self.limit] * len(points))
            
        # plot the data curve
        self.curve.setData(times,points)

        # current value readout in the title
        self.plot.setTitle(
            f"[{sum(points)/len(points): <4.4f}] [{points[-1]}] {series.name} {series.desc and (series.desc + ' ') or ''}")

    def get_props(self):
        return self.props

    def get_name():
        return "Plot"

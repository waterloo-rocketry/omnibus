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

        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.props = props

        if self.props == None:
            channel = self.prompt_user("Channel", "The channel you wish to listen to", "items", Parser.parsers.keys())
            all_series = [series.name for series in Parser.get_all_series(channel)]
            series = self.prompt_user("Series", "The series you wish to plot", "items", all_series)
            self.props = [channel, series]

        self.series = Parser.get_series(self.props[0], self.props[1])
        self.subscribe_to_series(self.series)

        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')

        self.widget = pg.PlotWidget(plotItem=self.plot)

        self.layout.addWidget(self.widget, 0, 0)

    def on_data_update(self, series):
        # update the displayed data
        self.curve.setData(series.times, series.points)

        # current value readout in the title
        self.plot.setTitle(
            f"{series.name} [{series.get_running_avg(): <4.4f}]")

        # round the time to the nearest GRAPH_STEP
        t = round(series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        self.plot.setXRange(t - config.GRAPH_DURATION + config.GRAPH_STEP,
                            t + config.GRAPH_STEP, padding=0)

    def get_props(self):
        print(self.props)
        return self.props
        

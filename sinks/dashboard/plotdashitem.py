from parsers import Parser
from pyqtgraph.Qt import QtWidgets

import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from dashboarditem import DashboardItem
import config


class PlotDashItem (DashboardItem):
    def __init__(self, props=None):
        self.series = None
        self.props = props
        if props is not None:
            self.series = Parser.get_series(props[0], props[1])
            self.plot = Plot(self.series)
        else:
            pass  # add a prompt here to do a get_series_all and fill the get_series! It's left as WIP for add button

        self.widget = pg.PlotWidget(plotItem=self.plot.plot)

    def get_props(self):
        return self.props

    def get_widget(self):
        return self.widget


class Plot:
    """
    Manages displaying and updating a single plot.
    """

    def __init__(self, series):
        self.series = series
        # update when data is added to the series
        self.series.register_update(self.update)

        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')

    def update(self):
        # update the displayed data
        self.curve.setData(self.series.times, self.series.points)

        # current value readout in the title
        self.plot.setTitle(
            f"{self.series.name} [{self.series.get_running_avg(): <4.4f}]")

        # round the time to the nearest GRAPH_STEP
        t = round(self.series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        self.plot.setXRange(t - config.GRAPH_DURATION + config.GRAPH_STEP,
                            t + config.GRAPH_STEP, padding=0)

    def __del__(self):
        print(self.series.name)
        self.series.register_update(None)

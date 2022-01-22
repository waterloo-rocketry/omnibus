import signal
import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import config

from parsers import Parser
from sinks.plot.tick_counter import TickCounter

import tick_counter


class Plotter:
    """
    Displays a grid of plots in a window
    """

    def __init__(self, callback):
        self.callback = callback  # called every frame to get new data

        # use 1 second of messages to determine which series are available
        # note: this is very temporary and will be replaced by dynamic plotter layouts soon
        print("Listening for series...")
        listen = time.time()
        while time.time() < listen + 1:
            callback()
        series = Parser.get_series()

        # try for a square layout
        columns = int(np.ceil(np.sqrt(len(series) + 1)))

        # window that lays out plots in a grid
        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter")
        self.win.resize(1000, 600)

        self.plots = []
        for i, s in enumerate(series):
            plot = Plot(s)
            self.plots.append(plot)
            # add the plot to a specific coordinate in the window
            self.win.addItem(plot.plot, i // columns, i % columns)
        self.fps = 0

        # Analytics & Tick Counter
        self.rates = []
        self.analytics = {"FPS": 0, "Running Average Duration (s)": 0}
        self.counter = TickCounter()

        self.exec()

    # called every frame
    def update(self):
        self.rates.append(time.time())
        if len(self.rates) > 50:
            self.rates.pop(0)
        if (time.time() - self.rates[0] > 0):
            self.fps = len(self.rates)/(time.time() - self.rates[0])

        self.analytics["FPS"] = str(round(self.fps, 2))
        self.analytics["Running Average Duration (s)"] = str(config.RUNNING_AVG_DURATION)
        self.counter.update(self.analytics)
        self.callback()

    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

        # make ctrl+c close the window
        signal.signal(signal.SIGINT, signal.SIG_DFL)

        pg.mkQApp().exec_()


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

import signal
import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

class Plotter:
    """
    Displays a grid of plots in a window
    """

    def __init__(self, series, callback):
        self.series = series
        self.callback = callback  # called every frame to get new data

        # try for a square layout
        columns = int(np.ceil(np.sqrt(len(self.series) + 1)))

        # window that lays out plots in a grid
        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter")
        self.win.resize(1000, 600)

        self.plots = []
        for i, s in enumerate(self.series):
            plot = Plot(s)
            self.plots.append(plot)
            # add the plot to a specific coordinate in the window
            self.win.addItem(plot.plot, i // columns, i % columns)
        self.fps = 0

        # adding a label masquerading as a graph
        self.labelText = ""
        self.label = LabelItem(self.labelText)
        self.win.addItem(self.label, columns - 1, len(self.series) % columns)
        self.rates = []

    # called every frame
    def update(self):
        self.labelText = ""
        self.rates.append(time.time())
        if len(self.rates) > 50:
            self.rates.pop(0)
        if (time.time() - self.rates[0] > 0):
            self.fps = len(self.rates)/(time.time() - self.rates[0])
            self.labelText= f"FPS: {self.fps: >4.2f}"
            print(f"\rFPS: {self.fps: >4.2f}  ", end='')
        #for s in self.series:
        #    self.labelText += ("\navg of " + s.name + f": {s.getRunningAvg(): <4.4f}")
        self.label.setText(self.labelText)
        
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
        self.avg = 0
        # update when data is added to the series
        self.series.register_update(self.update)

        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')
        
    def update(self):
        # update the displayed data
        self.curve.setData(self.series.times, self.series.points)

        # current value readout in the title
        self.plot.setTitle(f"{self.series.name} ({self.series.points[-1]:.1f}) [{self.series.get_running_avg(): <4.4f}]")
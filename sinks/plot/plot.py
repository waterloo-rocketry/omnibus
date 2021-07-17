import signal
import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

class Plotter:
    """
    Displays a grid of plots in a window
    """
    def __init__(self, series, callback):
        self.series = series
        self.callback = callback # called every frame to get new data

        # try for a square layout
        columns = int(np.ceil(np.sqrt(len(self.series))))

        # window that lays out plots in a grid
        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter")
        self.win.resize(1000, 600)

        self.plots = []
        for i, s in enumerate(self.series):
            plot = Plot(s)
            self.plots.append(plot)
            # add the plot to a specific coordinate in the window
            self.win.addItem(plot.plot, i // columns, i % columns)

        self.rates = []

    # called every frame
    def update(self):
        self.rates.append(time.time())
        if len(self.rates) > 50:
            self.rates.pop(0)
        print(f"\rFPS: {len(self.rates)/(time.time() - self.rates[0]): >4.0f}  ", end='')

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
        self.series.registerUpdate(self.update)

        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')

    def update(self):
        # update the displayed data
        self.curve.setData(self.series.times, self.series.points)

        # current value readout in the title
        self.plot.setTitle(f"{self.series.name} ({self.series.points[-1]:.1f})")

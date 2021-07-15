import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

from series import Series

class Plotter:
    def __init__(self, receiver):
        self.receiver = receiver

        columns = int(np.ceil(np.sqrt(len(Series.series))))

        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter")
        self.win.resize(1000, 600)

        self.plots = []
        for i, series in enumerate(Series.series):
            plot = Plot(series)
            self.plots.append(plot)
            self.win.addItem(plot.plot, i // columns, i % columns)

        self.rates = []

    def update(self):
        self.rates.append(time.time())
        if len(self.rates) > 50:
            self.rates.pop(0)
        print(f"\rFPS: {len(self.rates)/(time.time() - self.rates[0]): >4.0f}  ", end='')

        while msg := self.receiver.recv_message(0):
            Series.parse(msg.channel, msg.payload)

    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60
        pg.mkQApp().exec_()

class Plot:
    def __init__(self, series):
        self.series = series
        self.series.registerUpdate(self.update)

        self.plot = pg.PlotItem(title=series.name, left="Data", bottom="Seconds")
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')

    def update(self):
        self.curve.setData(self.series.times, self.series.points)

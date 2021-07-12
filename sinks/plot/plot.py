import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg

from omnibus import Receiver
from series import Series

# pg.setConfigOptions(antialias=True)

class Plotter:
    def __init__(self):
        self.receiver = Receiver("")

        SENSOR_COUNT = len(Series.series)

        columns = int(np.ceil(np.sqrt(SENSOR_COUNT)))
        rows = int(np.ceil(SENSOR_COUNT / columns))

        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter", size=(rows, columns))
        self.win.resize(1000, 600)

        self.plots = []
        self.curves = []
        for i, series in enumerate(Series.series):
            self.plots.append(self.win.addPlot(row=i // columns, col = i % columns,
                title=series.name, left="Data", bottom="Seconds"))
            self.curves.append(self.plots[-1].plot(series.times, series.points, pen='y'))

        self.rates = []

    def update(self):
        self.rates.append(time.time())
        if len(self.rates) > 50:
            self.rates.pop(0)
        print(f"\rFPS: {len(self.rates)/(time.time() - self.rates[0]): >4.0f}  ", end='')

        changed = False
        while msg := self.receiver.recv_message(0):
            changed |= Series.parse(msg.channel, msg.payload)
        if changed:
            for i, series in enumerate(Series.series):
                self.curves[i].setData(series.times, series.points)

    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60
        pg.mkQApp().exec_()

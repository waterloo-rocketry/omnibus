import time

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore

from omnibus import Receiver

SENSORS = 8

receiver = Receiver("tcp://localhost:5076", "DAQ")

win = pg.GraphicsLayoutWidget(show=True, title="DAQ")

pg.setConfigOptions(antialias=True)

plots = []
for row in range((SENSORS + 1) // 2):
    for col in range(2):
        plots.append(win.addPlot())
    win.nextRow()

curves = [plots[i].plot(pen='y') for i in range(SENSORS)]
data_streams = [[0 for _ in range(200)] for _ in range(SENSORS)]

last = 0


def update():
    global last
    dt = time.time()
    while data := receiver.recv(0):
        last, data = data

        for stream in data_streams:
            stream.pop(0)
            stream.append(data[i][0])

    for i in range(SENSORS):
        curves[i].setData(data_streams[i])

    print(f"\rFPS: {1/(time.time() - dt):.1f}  Lag: {time.time() - last:.2f}  ", end='')


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(60)

if __name__ == '__main__':
    pg.mkQApp().exec_()

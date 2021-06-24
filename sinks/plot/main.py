import sys

from omnibus import Receiver

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

import time

demo = True #Demo Mode
CHANNEL = "DAQ"
SENSOR_COUNT = 0
SENSORS = []

if (demo):
    CHANNEL = "DAQ"

    SENSOR_COUNT = 8

    # Sensor names; make sure this matches the names at the source!
    SENSORS = []
    for i in range(SENSOR_COUNT):
        SENSORS.append("Fake"+str(i))

    receiver = Receiver(CHANNEL)  # Receiving everything in DAQ channel

print("Connected to 0MQ server.")


win = pg.GraphicsLayoutWidget(show=True, title="Random Data Example")
win.resize(1000, 600)
win.setWindowTitle('pyqtgraph: Random Data Example')

pg.setConfigOptions(antialias=True)

# Layout Algorithm
plots = []

min_col = int(np.sqrt(SENSOR_COUNT))+1
min_row = (SENSOR_COUNT / min_col)+1
for i in range(0, min_row):
    for j in range(min_col*i, min_col*(i+1) if i != (min_row - 1) else SENSOR_COUNT):
        plots.append(win.addPlot(title=("Sensor: " + SENSORS[j])))
    if(i != min_row - 1):
        win.nextRow()

# plot generation
curves = [plots[i].plot(pen='y') for i in range(SENSOR_COUNT)]

graph_dp = 100 # 100 data points in the graph
data_streams = [[0 for _ in range(graph_dp)] for _ in range(SENSOR_COUNT)]  


def update():
    while new_data := receiver.recv(0):
        for i, sensor in enumerate(SENSORS):
            data_streams[i].pop(0)
            # Update Data Stream, currently only grabbing the first element in the payload obj
            data_streams[i].append(new_data["data"][sensor][0])
            # new_data is the received the payload object of class message (see omnibus.py)
            # whereby the payload is currently parsed as dictionary of a list (of a list)
            # the dictionary should have a key value pair where the key is the "data type", in this case "data"
            # the value is then a list of sensors, which consist of a list of data registered from each sensor
            # currently we are only plotting the first data point in each sensor
            curves[i].setData(data_streams[i])  # Update Graph Stream


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    pg.mkQApp().exec_()

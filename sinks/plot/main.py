from omnibus import Receiver

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np

import time
# Definitions are for demonstration purposes, please change them as needed.
CHANNEL = "DAQ"
SENSORS = ["P5 - Pneumatics", "P4 - Ox Fill", "P3 - Ox Tank", "P2 - CC",
           "Thrust", "SP1 - Nozzle", "FAST", "Omega S-Type", "T8 - Tank Heating"]
SENSOR_COUNT = len(SENSORS)

DOWNSAMPLE_RATE = 5  # 1/DOWNSAMPLE_RATE = % of data shown

GRAPH_DP = 30*10  # 10 points/second

receiver = Receiver(CHANNEL)  # Receiving everything in DAQ channel

print("Connected to 0MQ server.")

min_col = int(np.ceil(np.sqrt(SENSOR_COUNT)))
min_row = int(np.ceil(SENSOR_COUNT / min_col))
last_row_count = SENSOR_COUNT - min_col*(min_row - 1)

win = pg.GraphicsLayoutWidget(show=True, title="Data Example", size=(min_row, min_col))
win.resize(1000, 600)
win.setWindowTitle('pyqtgraph: Data Graph')

pg.setConfigOptions(antialias=True)

# Layout Algorithm
plots = []

for i in range(min_row - 1):
    for j in range(min_col):
        plots.append(win.addPlot(row=i, col=j, title=(
            "Sensor: " + SENSORS[i*min_col + j]), left="Data", bottom="Seconds"))

for j in range(last_row_count):
    plots.append(win.addPlot(row=min_row - 1, col=j,
                 title=("Sensor: " + SENSORS[min_col*(min_row - 1) + j]), left="Data", bottom="Seconds"))
# plot generation
times = [np.zeros(GRAPH_DP) for _ in range(SENSOR_COUNT)]
data_streams = [np.zeros(GRAPH_DP) for _ in range(SENSOR_COUNT)]

curves = [plots[i].plot(times[i], data_streams[i], pen='y') for i in range(SENSOR_COUNT)]

fps = 0

last = time.time()
start = time.time()
downsample = 0
first = True


def update():
    global fps, last, downsample, first

    latency = 0

    while new_data := receiver.recv(0):
        downsample += 1
        if downsample % DOWNSAMPLE_RATE != 0:  # 50 msgs/sec downsampled to 10 points/sec
            continue
        for i, sensor in enumerate(SENSORS):
            if sensor in new_data["data"]:
                if first:
                    data_streams[i].fill(new_data["data"][sensor][0])
                    times[i].fill(new_data["timestamp"] - start)
                # Update Data Stream, currently only grabbing the first element in the payload obj
                # shift every element in the data_stream back by 1 (except last one)
                data_streams[i][:-1] = data_streams[i][1:]
                # fill in last element with new data
                data_streams[i][-1] = new_data["data"][sensor][0]
                times[i][:-1] = times[i][1:]  # similar to above
                times[i][-1] = new_data["timestamp"] - start
                # new_data is the received the payload object of class message (see omnibus.py)
                # whereby the payload is currently parsed as dictionary (of datatypes) in a dictionary
                # which contains a sensor name - reading list key-value pair
                # See gist below
                """
                {
                    "timestamp": float,
                    "data": {
                        "Sensor 1": [float, float, ...],
                        "Sensor 2": [float, float, ...],
                        ...
                    }
                }
                """
                curves[i].setData(times[i], data_streams[i])  # Update Graph Stream

        first = False

        latency = time.time() - new_data["timestamp"]

    fps += 1

    if(time.time() - last > 1):  # Updates for every second
        last = time.time()
        win.setWindowTitle("pyqtgraph: Data Graph   " + f"Lag: {latency:.3f} FPS: {fps}")
        fps = 0


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

if __name__ == '__main__':
    pg.mkQApp().exec_()

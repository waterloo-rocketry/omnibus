from omnibus import Receiver

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import numpy as np

import time
# Definitions are for demonstration purposes, please change them as needed.
CHANNEL = "DAQ"
SENSORS = ["Fake0", "Fake1", "Fake2", "Fake3", "Fake4", "Fake5", "Fake6", "Fake7"]
SENSOR_COUNT = len(SENSORS)

GRAPH_DP = 100  # 100 data points in the graph

receiver = Receiver(CHANNEL)  # Receiving everything in DAQ channel

print("Connected to 0MQ server.")

min_col = int(np.sqrt(SENSOR_COUNT))+1
min_row = int(SENSOR_COUNT / min_col)+1
last_row_count = SENSOR_COUNT - min_col*(min_row - 1)

win = pg.GraphicsLayoutWidget(show=True, title="Data Example", size=(min_row, min_col))
win.resize(1000, 600)
win.setWindowTitle('pyqtgraph: Data Graph')

pg.setConfigOptions(antialias=True)

# Layout Algorithm
plots = []

for i in range(min_row - 1):
    for j in range(min_col):
        plots.append(win.addPlot(row=i, col=j, title=("Sensor: " + SENSORS[i*min_col + j]), left = "Data", bottom = "Time"))
        #win.addLabel(left = "Data", row=i, col=j)

for j in range(last_row_count):
    plots.append(win.addPlot(row=min_row - 1, col=j,
                 title=("Sensor: " + SENSORS[min_col*(min_row - 1) + i]), left = "Data", bottom = "Time"))
# plot generation
curves = [plots[i].plot(pen='y') for i in range(SENSOR_COUNT)]

data_streams = [[0 for _ in range(GRAPH_DP)] for _ in range(SENSOR_COUNT)]

fps = 0

last = time.time()

def update():
    global fps, last

    latency = 0
    
    while new_data := receiver.recv(0):
        for i, sensor in enumerate(SENSORS):
            if sensor in new_data["data"]:
                # Update Data Stream, currently only grabbing the first element in the payload obj
                data_streams[i].append(new_data["data"][sensor][0])
                # new_data is the received the payload object of class message (see omnibus.py)
                # whereby the payload is currently parsed as dictionary (of datatypes) in a dictionary (which contains a list of readings as value)
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
                data_streams[i].pop(0)
                curves[i].setData(data_streams[i])  # Update Graph Stream
            
        latency = time.time() - new_data["timestamp"]
        
    fps += 1

    if(time.time() - last > 0.2):
        last = time.time()
        print(f"\r lag:{latency:.3f} FPS:{fps * 5}", end="")
        fps = 0


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(16) # Capped at 60 Fps, 1000 ms / 16 ~= 60 

if __name__ == '__main__':
    pg.mkQApp().exec()

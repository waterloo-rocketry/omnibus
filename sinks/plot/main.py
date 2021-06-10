import sys

from omnibus import Receiver

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

import time

SENSOR = 4
SENSOR_ID = ["a","b","c","d"]

CHANNEL = "CH1"


receiver_list = Receiver("tcp://localhost:5076", CHANNEL)

print("Connected to 0MQ server.")


win = pg.GraphicsLayoutWidget(show=True, title="Random Data Example")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph: Random Data Example')

pg.setConfigOptions(antialias=True)

#Change the layouts here
plots =  [] #[win.addPlot(title=("Updating plot" + i))

min_col = np.ceil(np.sqrt(SENSOR))
min_row = np.ceil(SENSOR / min_col)
for i in range(0, min_row):
	for j in range(min_col*i, min_col*(i+1) if i != (min_row - 1) else SENSOR):
		plots.append(win.addPlot(title=("Updating sensor" + SENSOR_ID[j])))
	if(i != min_row - 1):
		win.nextRow()

curves = [plots[i].plot(pen='y') for i in range(SENSOR)]

data_streams = [[0 for _ in range(10)] for _ in range(SENSOR)] #10 data points

last = time.time()
fps = 0
def update(): #TBD Filtering by ID
	global curves, Receiver, plots, last, fps

	sent = time.time() + 1

	while new_data := Receiver.recv(0):
		for i in range(len(plots)):
			data_streams[i].pop(0)
			data_streams[i].append(new_data[i][0])
	
	for i in range(len(curves)):
		curves[i].setData(data_streams[i])

	fps += 1

	if(time.time() - last > 0.2):
		t = time.time()
		print(f"\r lag:{t - sent:.2f} FPS:{fps * 5}", end="")
		fps = 0

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    pg.mkQApp().exec_()
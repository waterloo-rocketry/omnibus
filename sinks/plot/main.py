import sys

from omnibus import Receiver

from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np

import time

CHANNEL = { #Channel Name (Sensor name): Array Index
	"CH1":1,
	"CH2":2,
	"CH3":3
}
CHANNEL_COUNT = len(CHANNEL)

receiver_list = Receiver("tcp://localhost:5076", "") #Receiving everything, filter by channel

print("Connected to 0MQ server.")


win = pg.GraphicsLayoutWidget(show=True, title="Random Data Example")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph: Random Data Example')

pg.setConfigOptions(antialias=True)

#dict for channel index to plot data

#Change the layouts here
plots =  [] #[win.addPlot(title=("Updating plot" + i))

min_col = np.ceil(np.sqrt(CHANNEL_COUNT))
min_row = np.ceil(CHANNEL_COUNT / min_col)
for i in range(0, min_row):
	for j in range(min_col*i, min_col*(i+1) if i != (min_row - 1) else CHANNEL_COUNT):
		plots.append(win.addPlot(title=("Updating sensor " + CHANNEL[j])))
	if(i != min_row - 1):
		win.nextRow()

curves = [plots[i].plot(pen='y') for i in range(CHANNEL_COUNT)]

data_streams = [[0 for _ in range(10)] for _ in range(CHANNEL_COUNT)] #10 data points

last = time.time()
fps = 0
def update():
	global curves, Receiver, plots, last, fps

	sent = time.time() + 1

	while new_data := Receiver.recv_message(0):
		if (channel_index := CHANNEL[new_data[channel]] != None):
			data_streams[channel_index].pop(0)
			data_streams[channel_index].append(new_data[payload[0]]) #Update Data Stream

			curves[channel_index].setData(data_streams[channel_index]) #Update Graph Stream
			break

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
import time

from omnibus import Receiver
import msgpack
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import zmq

context = zmq.Context()

Receiver = context.socket(zmq.SUB)
Receiver.connect("tcp://localhost:5076") # or whatever url the server is running on
Receiver.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all messages

print("Connected to 0MQ server.")

app = pg.mkQApp("test-random data")

win = pg.GraphicsLayoutWidget(show=True, title="Random Data Example")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph: Random Data Example')

pg.setConfigOptions(antialias=True)

plots =  [] #[win.addPlot(title=("Updating plot" + i))
for i in range(0,4):
	for j in range(4*i,4*i + 4):
		plots.append(win.addPlot(title=("Updating plot" + str(j))))
	if(i != 3):
		win.nextRow()

curves = [plots[i].plot(pen='y') for i in range(16)]

sent, new = msgpack.unpackb(Receiver.recv())

data_streams = [new[i] for i in range(len(new))] 

last = time.time()
fps = 0
def update():
	global curves, Receiver, ptr, plots, last, fps

	sent = time.time() + 1

	while Receiver.poll(1):
		sent, new = msgpack.unpackb(Receiver.recv())

		for i in range(len(plots)):
			data_streams[i].pop(0)
			data_streams[i].append(new[i][0])
	
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
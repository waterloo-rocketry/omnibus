import collections
import time
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import zmq

context = zmq.Context()

receiver = context.socket(zmq.SUB)
receiver.connect("tcp://localhost:5560") # or whatever url the server is running on
receiver.setsockopt(zmq.SUBSCRIBE, b"") # subscribe to all messages

print("Connected to 0MQ server.")

app = pg.mkQApp("test-random data")

win = pg.GraphicsLayoutWidget(show=True, title="Random Data Example")
win.resize(1000,600)
win.setWindowTitle('pyqtgraph: Random Data Example')

pg.setConfigOptions(antialias=True)

p6 = win.addPlot(title="Updating plot")
curve = p6.plot(pen='y')

ptr = 0
def update():
    global curve, receiver, ptr, p6
    sent, new = receiver.recv_pyobj()
    curve.setData(new[0])
    if ptr == 0:
        p6.enableAutoRange('xy', False)  ## stop auto-scaling after the first data set is plotted
    ptr += 1

timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(50)

if __name__ == '__main__':
    pg.mkQApp().exec_()

while True:
     sent, new = receiver.recv_pyobj()
     print(new)
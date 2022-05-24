import signal
import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import config
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from config import *
from parsers import Parser

from omnibus.util import TickCounter


class Plotter:
    """
    Displays a grid of plots in a window
    """

    def __init__(self, callback):
        self.callback = callback  # called every frame to get new data

        # use 1 second of messages to determine which series are available
        # note: this is very temporary and will be replaced by dynamic plotter layouts soon
        print("Listening for series...")
        listen = time.time()
        while time.time() < listen + 1:
            callback()
        series = Parser.get_series()

        # try for a square layout
        # columns = int(np.ceil(np.sqrt(len(series) + 1)))

        # window that lays out plots in a grid
        self.app = pg.mkQApp("Plotter UI")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Omnibus Plotter")
        self.win.resize(1000, 600)
        
        self.area = DockArea()
        self.win.setCentralWidget(self.area)

        """Make a master widget"""
        self.dm = Dock("Master Dock", size=(3, 3))
        self.wm = pg.LayoutWidget()
        self.saveBtn = QtWidgets.QPushButton('Save dock state')
        self.restoreBtn = QtWidgets.QPushButton('Restore dock state')
        self.restoreInitBtn = QtWidgets.QPushButton('Restore Initial state')
        self.restoreBtn.setEnabled(False)
        self.wm.addWidget(QtWidgets.QLabel("""Master Widget"""), row=0, col=0)
        self.wm.addWidget(self.saveBtn, row=1, col=0)
        self.wm.addWidget(self.restoreBtn, row=2, col=0)
        self.wm.addWidget(self.restoreInitBtn, row=3, col=0)
        self.dm.addWidget(self.wm)
        self.state = None
        self.initState = None

        def save():
            self.state = self.area.saveState()
            self.restoreBtn.setEnabled(True)
        def load():
            self.area.restoreState(self.state)
        def loadInit():
            self.area.restoreState(self.initState)
    
        self.saveBtn.clicked.connect(save)
        self.restoreBtn.clicked.connect(load)
        self.restoreInitBtn.clicked.connect(loadInit)

        self.plots = []
        self.anchor = [self.dm]
        self.area.addDock(self.dm, 'left')
        includedSeries = (s for s in series if s.name in INIT_SERIES_NAMES)
        for i, s in enumerate(includedSeries, start=1):
           # if s.name not in INIT_SERIES_NAMES:
           #     i -= 1
           #     continue
           # print(i)
           # print(self.anchor)
            plot = Plot(s)
            self.plots.append(plot)
            # add the plot to a specific coordinate in the window
            #if not(i):
            #    self.area.addDock(plot.dock, 'left')
            #    self.anchor.append(plot.dock)
            if (i < ITEMS_PER_ROW): 
                self.area.addDock(plot.dock, 'right', self.anchor[i-1])
                self.anchor.append(plot.dock)
                #plot.dock.resize(200,200)
                #plot.dock.setStretch(10,10)
                #self.area.addContainer("tab", plot.dock)
            else:
                self.area.addDock(plot.dock, 'bottom', self.anchor[i % ITEMS_PER_ROW])
                self.anchor[i % ITEMS_PER_ROW] = plot.dock
        
        self.initState = self.area.saveState()
        # add a viewbox with a textItem in it masquerading as a graph
        #self.textvb = self.win.addViewBox(
        #    col=columns - 1, row=len(series) % columns, enableMenu=False, enableMouse=False)
        #self.txitem = TextItem("", color=(255, 255, 255), anchor=(0.5, 0.5))
        #self.textvb.autoRange()
        # Center the Text, x set to 0.55 because 0.5 looks off-centre to the left somehow
        #self.txitem.setPos(0.55, 0.5)
        #self.textvb.addItem(self.txitem)

        self.counter = TickCounter(1)

        self.exec()

    # called every frame
    def update(self):
        self.counter.tick()

        # Filter to 5 frames per update on analytics
        if not(self.counter.tick_count() % 5):
            fps = self.counter.tick_rate()
            #self.txitem.setText(
            #    f"FPS: {fps: >4.2f}\nRunning Avg Duration: {config.RUNNING_AVG_DURATION} seconds")
            #print(f"\rFPS: {fps: >4.2f}", end='')

        self.callback()

    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

        # make ctrl+c close the window
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.win.show()
        pg.mkQApp().exec_()


class Plot:
    """
    Manages displaying and updating a single plot.
    """

    def __init__(self, series):
        self.series = series
        # update when data is added to the series
        self.series.register_update(self.update)

        self.plot = pg.PlotItem(title=self.series.name, left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()
        self.curve = self.plot.plot(self.series.times, self.series.points, pen='y')
        
        self.widget = pg.PlotWidget(plotItem = self.plot)
        self.dock = Dock("Dock - Plot "+self.series.name, size=(DOCK_SIZE_X,DOCK_SIZE_Y))
        self.dock.addWidget(self.widget)
    def update(self):
        # update the displayed data
        self.curve.setData(self.series.times, self.series.points)

        # current value readout in the title
        self.plot.setTitle(
            f"{self.series.name} [{self.series.get_running_avg(): <4.4f}]")

        # round the time to the nearest GRAPH_STEP
        t = round(self.series.times[-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        self.plot.setXRange(t - config.GRAPH_DURATION + config.GRAPH_STEP,
                            t + config.GRAPH_STEP, padding=0)

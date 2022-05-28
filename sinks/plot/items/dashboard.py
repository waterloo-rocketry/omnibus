import signal
import time
import pickle

import os.path
from os import path

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from parsers import Parser

from omnibus.util import TickCounter


class Dashboard:
    """
    Displays a grid of plots in a window
    """
    
    def load():
        savefile = open("savefile.sav", 'rb') 
        self.data = pickle.load(savefile)
        for i, item in data["items"]: # { 0: {...}, 1: ..., ...}
        if item["class"] == "PlotDashItem":
            p = PlotDashItem(item["props"])
            self.items.append[p]
            dock = Dock(name=i)
            dock.addWidget(p.child())
            self.area.addDock(dock)
        restoreLayout(file)
    
    def save():
        savefile = open("savefile.sav", 'wb')
        saveLayout()
        for k, item in self.items:
            self.data["items"][k] = {"props": item.save(), "class": type(item)}
        pickle.dump(self.data, savefile)
        savefile.close()

    def restoreLayout ():
        self.area.restoreState(data["layout"])

    def saveLayout ():
        self.data["layout"] = self.area.saveState()
    
    def __init__(self, callback):
        self.callback = callback  # called every frame to get new data
        self.data = {
            "items" : [],
            "layout" : None
        }
        # use 1 second of messages to determine which series are available
        # note: this is very temporary and will be replaced by dynamic plotter layouts soon
        print("Listening for series...")
        listen = time.time()
        while time.time() < listen + 1:
            callback()
        series = Parser.get_series()

        # window that lays out plots in a grid
        self.app = pg.mkQApp("Plotter UI")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Omnibus Plotter")
        self.win.resize(1000, 600)
        
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        
        self.items = []

        #if path.exists("savefile.sav") #This automatically loads
        #   load()

        """
        This commit removed the auto-layout generation along with the initialization of the plots respectively; refer to SHA 34561840
        """

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

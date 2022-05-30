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
from plotdashitem import PlotDashItem
from omnibus.util import TickCounter

class Dashboard:
    """
    Displays a grid of plots in a window
    """
    def restoreLayout(self):
        self.area.restoreState(self.data["layout"])

    def saveLayout(self):
        self.data["layout"] = self.area.saveState()
    
    def load(self):
        savefile = open("savefile.sav", 'rb') 
        self.data = pickle.load(savefile)
        for i, item in enumerate(self.data["items"]): # { 0: {...}, 1: ..., ...}
            if item["class"] == PlotDashItem:
                p = PlotDashItem(item["props"])
                self.items.append(p)
                dock = Dock(name=str(i))
                dock.addWidget(p.child())
                if self.anchor == None:
                    self.area.addDock(dock, 'right')
                    self.anchor = dock
                else:
                    self.area.addDock(dock, 'right', self.anchor)
                    self.anchor = dock
        self.restoreLayout()
   
    def save(self):
        savefile = open("savefile.sav", 'wb')
        self.saveLayout()
        self.data["items"] = []
        for k, item in enumerate(self.items):
            self.data["items"].append({"props": item.save(), "class": type(item)})
        pickle.dump(self.data, savefile)
        #for i in self.data["items"]:
        #    print(i)
        savefile.close()

    def add(self, itemtype, props):
        if itemtype == PlotDashItem:
            p = PlotDashItem(props)
            self.items.append(p)
            dock = Dock(name=str(len(self.items)-1))
            dock.addWidget(p.child())
            if self.anchor == None:
                self.area.addDock(dock, 'right')
                self.anchor = dock
            else:
                self.area.addDock(dock, 'right', self.anchor)
                self.anchor = dock

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
        #series = Parser.get_series()
        all_series = Parser.get_all_series()
        # window that lays out plots in a grid
        self.app = pg.mkQApp("Plotter UI")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Omnibus Plotter")
        self.win.resize(1000, 600)
        
        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        self.anchor = None
        self.items = []
        sample_props = [["DAQ", "Fake0"], ["DAQ", "Fake1"]]
        self.add(PlotDashItem, sample_props[0])
        self.add(PlotDashItem, sample_props[1])
        self.save()
        #self.load()
        
        """
        Sample add function is provided, use self.load to restore save file
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

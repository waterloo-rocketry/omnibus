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
from can_display import CanDisplayDashItem
from omnibus.util import TickCounter


class Dashboard:
    """
    Displays a grid of plots in a window
    """

    def restoreLayout(self):
        self.area.restoreState(self.data["layout"])

    def saveLayout(self):
        self.data["layout"] = self.area.saveState()

    def load(self, file="savefile.sav"):
        self.area = DockArea() #Clears all docks by throwing away the entire dockarea
        self.win.setCentralWidget(self.area)
        self.anchor = None 
        self.items = []

        with open(file, 'rb') as savefile:
            self.data = pickle.load(savefile)
        
        for i, item in enumerate(self.data["items"]):  # { 0: {...}, 1: ..., ...}
            self.add(item["class"], item["props"])
        self.restoreLayout()

    def save(self, file="savefile.sav"):
        self.saveLayout()
        self.data["items"] = []
        for k, item in enumerate(self.items):
            self.data["items"].append({"props": item.get_props(), "class": type(item)})
        with open(file, 'wb') as savefile:
            pickle.dump(self.data, savefile)

    def add(self, itemtype, props):
        p = itemtype(props)  # Please pass in the itemtype of the object (no quotes!) in itemtype
        # If it is a newly added plot from button, please set props to nothing and set props
        # via prompt called at initialization of plotDashItem, since get_all_series need to be
        # called at initialization of newly added plot (that is not loaded from file)
        self.items.append(p)
        dock = Dock(name=str(len(self.items)-1))
        dock.addWidget(p.get_widget())
        if self.anchor == None:
            self.area.addDock(dock, 'right')
            self.anchor = dock
        else:
            self.area.addDock(dock, 'right', self.anchor)
            self.anchor = dock

    def __init__(self, callback):
        self.callback = callback  # called every frame to get new data
        self.data = {
            "items": [],
            "layout": None
        }
        
        # window that lays out plots in a grid
        self.app = pg.mkQApp("Dashboard")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle("Omnibus Dashboard")
        self.win.resize(1000, 600)

        self.area = DockArea()
        self.win.setCentralWidget(self.area)
        self.anchor = None
        self.items = []
        sample_props = [["DAQ", "Fake0"], ["DAQ", "Fake1"]]

        print("Listening for series...")
        listen = time.time()
        while time.time() < listen + 1:
            callback()
            
        series = Parser.get_all_series()

        for elem in series:
            self.add(PlotDashItem, ["DAQ", elem.name])

        self.add(CanDisplayDashItem, None)
        self.canDisplayItemIndex = len(series)
        self.save()
        #self.load() #use this function to restore from save file

        self.counter = TickCounter(1)

        self.exec()

    # called every frame
    def update(self):
        self.counter.tick()

        self.items[self.canDisplayItemIndex].update()

        # Filter to 5 frames per update on analytics
        if not(self.counter.tick_count() % 5):
            fps = self.counter.tick_rate()
            # self.txitem.setText(
            #    f"FPS: {fps: >4.2f}\nRunning Avg Duration: {config.RUNNING_AVG_DURATION} seconds")
            #print(f"\rFPS: {fps: >4.2f}", end='')
            """
            To Do: TextDashItem
            """

        self.callback()

    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60
        
        # make ctrl+c close the window
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.win.show()
        pg.mkQApp().exec_()

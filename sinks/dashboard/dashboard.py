import signal
import time
import pickle

import os.path
from os import path
import sys

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QGridLayout, QMenuBar

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from parsers import Parser
from plotdashitem import PlotDashItem
from omnibus.util import TickCounter
import sip

# "Temorary Global Constant"

item_types = [
    PlotDashItem,
]


class Dashboard(QtWidgets.QWidget):
    """
    Displays a grid of plots in a window
    """

    def restoreLayout(self):
        self.area.restoreState(self.data["layout"])

    def saveLayout(self):
        self.data["layout"] = self.area.saveState()

    def load(self, file="savefile.sav"):
        # Clears all docks by throwing away the entire dockarea
        self.layout.removeWidget(self.area)
        self.area.deleteLater()
        del self.area

        # Delete all plot widgets
        for item in self.items:
            print(item)
            sip.delete(item.get_widget())

        self.area = DockArea()
        self.layout.addWidget(self.area)

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
        dock = Dock(name=str(len(self.items)-1), closable=True)

        # Bit of a sussy baka, but this is the only way we can really get control over
        # how the thing closes
        def custom_callback(dock_arg):
            if self.anchor == dock_arg:
                self.anchor = None

        dock.sigClosed.connect(custom_callback)

        dock.addWidget(p.get_widget())
        if self.anchor == None:
            self.area.addDock(dock, 'right')
            self.anchor = dock
        else:
            self.area.addDock(dock, 'right', self.anchor)
            self.anchor = dock

    def __init__(self, callback):
        # Initilize Super Class
        QtWidgets.QWidget.__init__(self)


        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Attach Menu

        menubar = QMenuBar()
        self.layout.addWidget(menubar, 0, 0)

        # Add action
        add_item_menu = menubar.addMenu("Add Item")
        add_item_actions = []

        for dock_item_type in item_types:
            new_action = add_item_menu.addAction(dock_item_type.__name__)
            new_action.triggered.connect(self.prompt_and_add(dock_item_type))
            add_item_actions.append(new_action)

        save_layout_action = menubar.addAction("Save")

        def save_ignore_args(arg):
            self.save()

        save_layout_action.triggered.connect(save_ignore_args)

        restore_layout_action = menubar.addAction("Reset")

        def load_ignore_args(arg):
            self.load()

        restore_layout_action.triggered.connect(load_ignore_args)

        self.callback = callback  # called every frame to get new data
        self.data = {
            "items": [],
            "layout": None
        }
        
        #self.win = QtWidgets.QMainWindow()
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(1000, 600)

        # Dock Area
        self.area = DockArea()
        self.anchor = None
        self.items = []
        sample_props = [["DAQ", "Fake0"], ["DAQ", "Fake1"]]

        # Container
        self.layout.addWidget(self.area)

        # Adding widgets
        self.add(PlotDashItem, sample_props[0])
        self.add(PlotDashItem, sample_props[1])
        self.save()

        self.counter = TickCounter(1)

    # called every frame
    def update(self):
        self.counter.tick()

        # Filter to 5 frames per update on analytics
        if not(self.counter.tick_count() % 5):
            fps = self.counter.tick_rate()

        self.callback()

    def prompt_and_add(self, itemtype):
        # The parameter is some kind of boolean
        def return_func(param):
            self.add(itemtype, ["DAQ", "Fake2"])

        return return_func


def dashboard_driver(callback):
    app = QtWidgets.QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QtCore.QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.show()
    sys.exit(app.exec_())
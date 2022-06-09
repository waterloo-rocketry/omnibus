import pickle
import os
import time
import sys

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QGridLayout, QMenuBar

from parsers import Parser
from plotdashitem import PlotDashItem
from omnibus.util import TickCounter

# "Temorary Global Constant"

item_types = [
    PlotDashItem,
]

filename = "savefile.sav"


class Dashboard(QtWidgets.QWidget):
    """
    Displays a grid of plots in a window
    """

    def __init__(self, callback):
        # Initilize Super Class
        QtWidgets.QWidget.__init__(self)

        # called every frame to get new data
        self.callback = callback

        # To address bugs
        print("Listening for series...")
        listen = time.time()
        while time.time() < listen + 1:
            callback()
        
        # Data used for saving and 
        # restoring
        self.data = {
            "items": [],
            "layout": None
        }

        # A list of all items in the dashboard
        self.docks = []
        # Experimental
        self.saved_items = []

        # Create the QT GUI which will be the dashboard
        # To do, find a way to move all of this to
        # another file
        ###############################################
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(1000, 600)

        # Create GridLayout, will be
        # Adding components to this as
        # time goes on
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Add a menu bar to the layout
        menubar = QMenuBar()
        self.layout.addWidget(menubar, 0, 0)

        # Create a sub menu which will be used
        # to add items to our dash board.
        # For all dash items we support, there will
        # be a corresponding action to add that item 
        add_item_menu = menubar.addMenu("Add Item")
        
        for dock_item_type in item_types:
            new_action = add_item_menu.addAction(dock_item_type.__name__)
            new_action.triggered.connect(self.prompt_and_add(dock_item_type))

        # Add an action to the menu bar to save the 
        # layout of the dashboard.
        save_layout_action = menubar.addAction("Save")
        save_layout_action.triggered.connect(self.save)

        # Add an action to the menu bar to load the
        # layout of the dashboard.
        restore_layout_action = menubar.addAction("Reset")
        restore_layout_action.triggered.connect(self.load)

        # Create the Dock Area which will house all of the items
        self.area = DockArea()
        self.layout.addWidget(self.area)

        # Restore last save state
        self.load()

        self.counter = TickCounter(1)

    def restoreLayout(self):
        if self.data["layout"]:
            self.area.restoreState(self.data["layout"])

    def saveLayout(self):
        self.data["layout"] = self.area.saveState()

    def load(self):
        for dock in self.docks:
            item = dock.widgets[0]
            item.unsubscribe_to_all()

        # Clears all docks by throwing away the entire dockarea
        self.layout.removeWidget(self.area)
        self.area.deleteLater()
        del self.area

        self.area = DockArea()
        self.layout.addWidget(self.area)

        self.docks = []

        if os.path.isfile(filename):
            with open(filename, 'rb') as savefile:
                self.data = pickle.load(savefile)
        
        for i, item in enumerate(self.data["items"]):  # { 0: {...}, 1: ..., ...}
            self.add(item["class"], item["props"])
        self.restoreLayout()

    def save(self):
        self.saveLayout()
        self.data["items"] = []
        for dock in self.docks:
            item = dock.widgets[0]
            self.data["items"].append({"props": item.get_props(), "class": type(item)})
        with open(filename, 'wb') as savefile:
            pickle.dump(self.data, savefile)

    def add(self, itemtype, props):
        p = itemtype(props)  # Please pass in the itemtype of the object (no quotes!) in itemtype
        # If it is a newly added plot from button, please set props to nothing and set props
        # via prompt called at initialization of plotDashItem, since get_all_series need to be
        # called at initialization of newly added plot (that is not loaded from file)
        dock = Dock(name=str(len(self.docks)-1), closable=True)

        # Bit of a sussy baka, but this is the only way we can really get control over
        # how the thing closes
        def custom_callback(dock_arg):
            p.unsubscribe_to_all()
            self.docks = [dock for dock in self.docks if dock.widgets[0] != p]

        dock.sigClosed.connect(custom_callback)

        dock.addWidget(p)
        if len(self.docks):
            self.area.addDock(dock, 'right', self.docks[-1])
        else:
            self.area.addDock(dock, 'right')

        self.docks.append(dock)

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
            self.add(itemtype, None)

        return return_func


def dashboard_driver(callback):
    app = QtWidgets.QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QtCore.QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.show()
    sys.exit(app.exec_())
import pickle
import os
import time
import sys

from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtGui import QVBoxLayout, QMenuBar

from items.plot_dash_item import PlotDashItem
from items.can_message_table import CanMsgTableDashItem
from omnibus.util import TickCounter
from utils import prompt_user

# "Temporary Global Constant"

item_types = [
    PlotDashItem,
    CanMsgTableDashItem,
]


class Dashboard(QtWidgets.QWidget):
    """
    Displays a grid of plots in a window
    """

    def __init__(self, callback):
        # Initilize Super Class
        QtWidgets.QWidget.__init__(self)

        # called every frame to get new data
        self.callback = callback

        # The file from which the dashboard is loaded
        self.filename = "savefile.sav"
        self.filename_cache = [self.filename]

        # A list of all docks in the dock area
        # doubles as a list of all the items in
        # the dashboare by making use of
        # item = dock.widgets[0]
        self.docks = []

        # Create the QT GUI which will be the dashboard
        # To do, find a way to move all of this to
        # another file
        ###############################################
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(1000, 600)

        # Create GridLayout, will be
        # Adding components to this as
        # time goes on
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Add a menu bar to the layout
        menubar = QMenuBar(self)

        # Create a sub menu which will be used
        # to add items to our dash board.
        # For all dash items we support, there will
        # be a corresponding action to add that item
        add_item_menu = menubar.addMenu("Add Item")

        def prompt_and_add(i):
            def ret_func():
                self.add(item_types[i](None))
            return ret_func

        for i in range(len(item_types)):
            new_action = add_item_menu.addAction(item_types[i].get_name())
            new_action.triggered.connect(prompt_and_add(i))

        # Add an action to the menu bar to save the
        # layout of the dashboard.
        add_save_menu = menubar.addMenu("Save")
        save_layout_action = add_save_menu.addAction("Save Current Config")
        save_layout_action.triggered.connect(self.save)

        # Add an action to the menu bar to load the
        # layout of the dashboard.
        add_restore_menu = menubar.addMenu("Load")
        restore_layout_action = add_restore_menu.addAction("Load from File")
        restore_layout_action.triggered.connect(self.load)

        # Add an action to the menu bar to open a file
        add_open_menu = menubar.addMenu("Open")
        open_file_action = add_open_menu.addAction("Open File")
        open_file_action.triggered.connect(self.switch)

        self.layout.setMenuBar(menubar)

        # Create the Dock Area which will house all of the items
        self.area = DockArea()
        self.layout.addWidget(self.area)

        # Restore last save state
        self.load()

        self.counter = TickCounter(1)

    def load(self):
        # First, we need to clear all the
        # docks currently on the screen.

        # First, make sure that the dash
        # items within the docks are not
        # registered with any series
        for dock in self.docks:
            item = dock.widgets[0]
            item.unsubscribe_to_all()

        # Second, remove the entire dock area,
        # thereby deleting all of the docks
        # contained within
        self.layout.removeWidget(self.area)
        self.area.deleteLater()
        del self.area

        # Now we recreate the dock area,
        # ahearing to the layout specified in
        # the save file

        # Create a new dock area
        self.area = DockArea()
        self.layout.addWidget(self.area)

        # re-populate our dash area using
        # the save file
        self.docks = []

        # if the save file exists, set our
        # data variable to it
        if os.path.isfile(self.filename):
            with open(self.filename, 'rb') as savefile:
                data = pickle.load(savefile)
        else:
            data = {
                "items": [],
                "layout": None
            }

        # for every item specified by the save file,
        # add that item back to the dock
        for i, item in enumerate(data["items"]):  # { 0: {...}, 1: ..., ...}
            self.add(item["class"](item["props"]))

        # restore the layout
        if data["layout"]:
            self.area.restoreState(data["layout"])

    def save(self):
        data = {
            "items": [],
            "layout": None
        }
        # The way that self.area.saveState() works
        # is by assigning properties to each dock
        # base on its name. This means we need to
        # set the names in such a way that when
        # the docks are re-added, the names align
        # therefore, we set the name of each dock
        # to its index within docks
        for i in range(len(self.docks)):
            self.docks[i]._name = str(i)
            self.docks[i].label.setText(str(i))

        # store layout data to data["layout"]
        data["layout"] = self.area.saveState()

        # store data on the specific dash items to
        # data["items"]
        data["items"] = []
        for dock in self.docks:
            item = dock.widgets[0]
            data["items"].append({"props": item.get_props(), "class": type(item)})

        # Save to the save file
        with open(self.filename, 'wb') as savefile:
            pickle.dump(data, savefile)

    def add(self, dashitem):
        # Create a new dock to be added to the dock area
        dock = Dock(f"{len(self.docks)}", closable=True)

        # Bit of a sussy baka, but this is the only way we can really get control over
        # how the thing closes. In future, I might make a class method that returns
        # this. Right now, not a priority.

        # Create a call back to execute when docks close to ensure cleaning up is done
        # right
        def custom_callback(dock_arg):
            dashitem.unsubscribe_to_all()
            self.docks = [dock for dock in self.docks if dock.widgets[0] != dashitem]

        dock.sigClosed.connect(custom_callback)

        # add widget to dock
        dock.addWidget(dashitem)

        # add dock to dock area
        self.area.addDock(dock, 'right')

        # add dock to dock list
        self.docks.append(dock)

    def switch(self):
        self.save()
        filename = prompt_user(
                self,
                "New File Name",
                "Enter the name of the file which you wish to load",
                "items",
                self.filename_cache,
                True
            )

        if filename == None:
            return


        # If the filename entered is not valid
        # this exhibits the behaviour of creating
        # a new one

        if filename not in self.filename_cache:
            self.filename_cache.append(filename)

        self.filename = filename
        self.load()

    # called every frame
    def update(self):
        self.counter.tick()

        # Filter to 5 frames per update on analytics
        if not(self.counter.tick_count() % 5):
            fps = self.counter.tick_rate()

        self.callback()


def dashboard_driver(callback):
    app = QtWidgets.QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QtCore.QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.show()
    sys.exit(app.exec_())

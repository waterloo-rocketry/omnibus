import os
import sys
import json

from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QPainter
from pyqtgraph.Qt.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QApplication,
    QWidget,
    QMenuBar,
    QVBoxLayout,
    QGraphicsItem,
    QGraphicsRectItem
)
from items import registry
from omnibus.util import TickCounter
from utils import prompt_user

# These need to be imported to be added to the registry
from items.plot_dash_item import PlotDashItem
from items.can_message_table import CanMsgTableDashItem


# Custom class derived from QGraphicsView to capture mouse
# wheel events by overriding the wheelEvent function
class MyQGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        # Initialize the super class
        super(MyQGraphicsView, self).__init__(parent)
        self.zoomed = 1

    def zoom(self, direction: str):
        # Zoom factor
        zoomInFactor = 1.1
        zoomOutFactor = 1/zoomInFactor

        # Zooms to the position of the mouse
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        if direction.lower() == "in":
            zoomFactor = zoomInFactor
        elif direction.lower() == "out":
            zoomFactor = zoomOutFactor

        # Scale the scene
        self.zoomed *= zoomFactor
        self.scale(zoomFactor, zoomFactor)

    def wheelEvent(self, event):
        # Zoom if Shift is held, otherwise scroll
        if event.modifiers() == Qt.ShiftModifier:
            # Determine zoom in/out by how much the wheel moves
            angle = event.angleDelta()
            if angle.x() > 0 or angle.y() > 0:
                self.zoom("in")
            elif angle.x() < 0 or angle.y() < 0:
                self.zoom("out")
        else:
            super(QGraphicsView, self).wheelEvent(event)


# Custom Dashboard class derived from QWidget
class Dashboard(QWidget):
    def __init__(self, callback):
        # Initialize the super class
        super().__init__()

        # Called every frame to get new data
        self.callback = callback

        # Dictionary to map rectitems to widgets
        # and dashitems
        self.widgets = {}

        # Keep track of if editing is allowed
        self.locked = False

        # The file from which the dashboard is loaded
        self.filename = "savefile.json"
        self.filename_cache = [self.filename]

        # Create a GUI
        self.width = 1100
        self.height = 700
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(self.width, self.height)

        # Create a large scene underneath the view
        self.scene = QGraphicsScene(0, 0, self.width*100, self.height*100)

        # Create a grid layout
        self.layout = QVBoxLayout()

        # Create a menubar for actions
        menubar = QMenuBar(self)

        # List to keep track of menu bar action that
        # can be disabled when dashboard is locked
        self.actions = []

        # Create a sub menu which will be used
        # to add items to our dash board.
        # For all dash items we support, there will
        # be a corresponding action to add that item
        add_item_menu = menubar.addMenu("Add Item")

        def prompt_and_add(i):
            def ret_func():
                # props for a single item is contained in a dictionary
                props = registry.get_items()[i].prompt_for_properties(self)
                if props:
                    if isinstance(props, list):
                        for item in props:
                            self.add(registry.get_items()[i](item))
                    else:
                        self.add(registry.get_items()[i](props))
            return ret_func

        for i in range(len(registry.get_items())):
            new_action = add_item_menu.addAction(registry.get_items()[i].get_name())
            new_action.triggered.connect(prompt_and_add(i))
            self.actions.append(new_action)

        # Add an action to the menu bar to save the
        # layout of the dashboard.
        add_save_menu = menubar.addMenu("Save")
        save_layout_action = add_save_menu.addAction("Save Current Config")
        save_layout_action.triggered.connect(self.save)
        self.actions.append(save_layout_action)

        # Add an action to the menu bar to load the
        # layout of the dashboard.
        add_restore_menu = menubar.addMenu("Load")
        restore_layout_action = add_restore_menu.addAction("Load from File")
        restore_layout_action.triggered.connect(self.load)
        self.actions.append(restore_layout_action)

        # Add an action to the menu bar to open a file
        add_open_menu = menubar.addMenu("Open")
        open_file_action = add_open_menu.addAction("Open File")
        open_file_action.triggered.connect(self.switch)
        self.actions.append(open_file_action)

        # Add an action to the menu bar to lock/unlock
        # the dashboard
        add_open_menu = menubar.addMenu("Lock")
        lock_action = add_open_menu.addAction("Lock Dashboard")
        lock_action.triggered.connect(self.lock)
        self.actions.append(lock_action)
        unlock_action = add_open_menu.addAction("Unlock Dashboard")
        unlock_action.triggered.connect(self.unlock)

        self.layout.setMenuBar(menubar)

        # Set the counter
        self.counter = TickCounter(1)

        # Create the view and add it to the widget
        self.view = MyQGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setRenderHints(QPainter.Antialiasing)
        self.layout.addWidget(self.view)
        self.setLayout(self.layout)

    # Method to add widgets
    def add(self, dashitem, pos=None):
        # Add the dash item to the scene and get
        # its proxy widget and dimension
        proxy = self.scene.addWidget(dashitem)
        height = proxy.size().height()
        width = proxy.size().width()

        # If a position is given, use it. If not, position
        # the widget in the center of the current view
        if pos:
            mapped = self.view.mapToScene(pos[0], pos[1])
            xpos = mapped.x()
            ypos = mapped.y()
        else:
            # Get the current size of the view area and map
            # it to the underlying scene
            viewport = self.view.viewport().size()
            view_xpos = viewport.width()/2
            view_ypos = viewport.height()/2

            mapped = self.view.mapToScene(view_xpos, view_ypos)

            # Center the widget in the view. Qt sets position
            # based on the upper left corner, so subtract
            # half the width and height of the widget to
            # center the center
            xpos = mapped.x() - (width/2)
            ypos = mapped.y() - (height/2)

        proxy.setPos(xpos, ypos)
        proxy.setFocusPolicy(Qt.NoFocus)

        # Create a rectangle around the proxy widget
        # to make it movable and selectable
        rect = QGraphicsRectItem(xpos-1, ypos-1, width+1, height+1)
        proxy.setParentItem(rect)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.scene.addItem(rect)

        # Map the proxy widget and dashitem to the rectitem
        self.widgets[rect] = [proxy, dashitem]

    # Method to remove a widget
    def remove(self, item):
        # Remove the rectangle from the scene,
        # delete the proxy widget and tell the
        # dashitem to stop sending data
        components = self.widgets[item]
        proxy = components[0]
        dashitem = components[1]
        self.scene.removeItem(item)
        proxy.deleteLater()
        dashitem.on_delete()

    # Method to remove all widgets
    def remove_all(self):
        for item in self.widgets:
            self.remove(item)

        # Clear the mapping list. This can't be
        # done while iterating through the dict
        # because it changes the length and causes
        # a RunTime Error
        self.widgets = {}

    # Method to load layout from file
    def load(self):
        # First remove all the current widgets
        self.remove_all()

        # Then load the data from the savefile
        if os.path.exists(self.filename):
            with open(self.filename, "r") as savefile:
                data = json.load(savefile)
        else:
            return

        # Add every widget in the data
        for widget in data["widgets"]:
            # ObjectTypes can't be converted to JSON
            # See the save method
            for item_type in registry.get_items():
                if widget["class"] == item_type.get_name():
                    self.add(item_type(widget["props"]), widget["pos"])
                    break

        # Set the zoom
        curr_zoom = self.view.zoomed
        self.view.scale(1/curr_zoom, 1/curr_zoom)
        new_zoom = data["zoom"]
        self.view.scale(new_zoom, new_zoom)
        self.view.zoomed = new_zoom

    # Method to save current layout to file
    def save(self):
        data = {"zoom": self.view.zoomed, "widgets": []}
        for items in self.widgets.values():
            # Get the proxy widget and dashitem
            proxy = items[0]
            dashitem = items[1]

            # Get the coordinates of the proxy widget
            # on the view not the scene
            scenepos = proxy.scenePos()
            viewpos = self.view.mapFromScene(scenepos)

            # Add the position, dashitem name and dashitem props
            for item_type in registry.get_items():
                if type(dashitem) == item_type:
                    data["widgets"].append({"class": item_type.get_name(),
                                            "props": dashitem.get_props(),
                                            "pos": [viewpos.x(), viewpos.y()]})
                    break

        # Write data to savefile
        with open(self.filename, "w") as savefile:
            json.dump(data, savefile)

    # Method to switch to a layout in a different file
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

    # Method to lock dashboard
    def lock(self):
        self.locked = True
        self.setWindowTitle("Omnibus Dashboard - LOCKED")

        # Disable menu actions
        for menu_item in self.actions:
            menu_item.setEnabled(False)

        # Disable selecting and moving plots
        for rect in self.widgets:
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=False)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)

    # Method to unlock dashboard
    def unlock(self):
        self.locked = False
        self.setWindowTitle("Omnibus Dashboard")

        # Enable menu actions
        for menu_item in self.actions:
            menu_item.setEnabled(True)

        # Enable selecting and moving plots
        for rect in self.widgets:
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=True)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=True)

    # Method to get new data for widgets
    def update(self):
        self.counter.tick()
        self.callback()

    # Method to center the view
    def reset(self):
        # Reset the zoom
        self.view.scale(1/self.view.zoomed, 1/self.view.zoomed)
        self.view.zoomed = 1

        # Center the view
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        self.view.centerOn(scene_width/2, scene_height/2)

    # Method to capture key presses
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Backspace and not self.locked:
            # Delete all selected items
            for item in self.scene.selectedItems():
                self.remove(item)
                self.widgets.pop(item)
        elif event.modifiers() == Qt.ControlModifier:
            # Forward event to proper handler
            match event.key():
                case Qt.Key_Equal:
                    self.view.zoom("in")
                case Qt.Key_Minus:
                    self.view.zoom("out")
                case Qt.Key_0:
                    self.reset()


# Function to launch the dashboard
def dashboard_driver(callback):
    app = QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.show()
    dash.load()
    app.exec()

import os
import sys
import json
import signal

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
from utils import prompt_user, ConfirmDialog

# These need to be imported to be added to the registry
from items.plot_dash_item import PlotDashItem
from items.can_message_table import CanMsgTableDashItem
from items.can_sender.can_sender import CanMsgSndr #idk why this is needed but it doesn't show in dropdown otherwise
from omnibus.util import TickCounter
from utils import prompt_user, ConfirmDialog

# These need to be imported to be added to the registry
from items.plot_dash_item import PlotDashItem
from items.plot_3D_orientation import Orientation3DDashItem
from items.plot_3D_position import Position3DDashItem
from items.can_message_table import CanMsgTableDashItem
from items.can_sender import CanSender

# Custom class derived from QGraphicsView to capture mouse
# wheel events by overriding the wheelEvent function
class MyQGraphicsView(QGraphicsView):
    def __init__(self, parent=None):
        # Initialize the super class
        super(MyQGraphicsView, self).__init__(parent)
        self.zoomed = 1.0

        # Zooms to the position of the mouse
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def zoom(self, angle: int):
        # Create the zoom factor based on the angle
        zoomFactor = 1 + angle*0.001

        # Scale the scene
        self.zoomed *= zoomFactor
        self.scale(zoomFactor, zoomFactor)

    def wheelEvent(self, event):
        # Zoom if ctrl/cmd is held
        # Scroll horizontally if shift is held
        # Scroll vertically otherwise
        angle = event.angleDelta()
        if event.modifiers() == Qt.ControlModifier:
            self.zoom(angle.y())
        elif event.source() == Qt.MouseEventNotSynthesized:
            # mouse wheel event
            scroll_sensitivity_factor = 1/3  # feels good constant
            if event.modifiers() == Qt.ShiftModifier:
                numDegrees = angle.y() * scroll_sensitivity_factor
                value = self.horizontalScrollBar().value()
                self.horizontalScrollBar().setValue(value + numDegrees)
            else:
                numDegrees = angle.y() * scroll_sensitivity_factor
                value = self.verticalScrollBar().value()
                self.verticalScrollBar().setValue(value + numDegrees)
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
        self.lockableActions = []

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
            self.lockableActions.append(new_action)

        # Add an action to the menu bar to save the
        # layout of the dashboard.
        add_save_menu = menubar.addMenu("Save")
        save_layout_action = add_save_menu.addAction("Save Current Config")
        save_layout_action.triggered.connect(self.save)
        self.lockableActions.append(save_layout_action)

        # Add an action to the menu bar to load the
        # layout of the dashboard.
        add_restore_menu = menubar.addMenu("Load")
        restore_layout_action = add_restore_menu.addAction("Load from File")
        restore_layout_action.triggered.connect(self.load)
        self.lockableActions.append(restore_layout_action)

        # Add an action to the menu bar to open a file
        add_open_menu = menubar.addMenu("Open")
        open_file_action = add_open_menu.addAction("Open File")
        open_file_action.triggered.connect(self.switch)
        self.lockableActions.append(open_file_action)

        # Add an action to the menu bar to lock/unlock
        # the dashboard
        add_lock_menu = menubar.addMenu("Lock")
        lock_action = add_lock_menu.addAction("Lock Dashboard")
        lock_action.triggered.connect(self.lock)
        self.lockableActions.append(lock_action)
        unlock_action = add_lock_menu.addAction("Unlock Dashboard")
        unlock_action.triggered.connect(self.unlock)

        # Add an action to the menu bar to display a
        # help box
        add_help_menu = menubar.addMenu("Help")
        help_action = add_help_menu.addAction("Omnibus Help")
        help_action.triggered.connect(self.help)

        self.layout.setMenuBar(menubar)

        # Set the counter
        self.counter = TickCounter(1)

        # Create the view and add it to the widget
        self.view = MyQGraphicsView(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setRenderHints(QPainter.Antialiasing)
        self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
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
        if not pos:
            # Get the current size of the view area and map
            # it to the underlying scene
            mapped = self.view.mapToScene(self.view.width()/2, self.view.height()/2)

            # Center the widget in the view. Qt sets position
            # based on the upper left corner, so subtract
            # half the width and height of the widget to
            # center the center
            pos = [mapped.x() - (width/2), mapped.y() - (height/2)]

        proxy.setPos(pos[0], pos[1])
        proxy.setFocusPolicy(Qt.NoFocus)

        # Create a rectangle around the proxy widget
        # to make it movable and selectable
        rect = QGraphicsRectItem(pos[0]-1, pos[1]-1, width+1, height+1)
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
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r") as savefile:
            data = json.load(savefile)

        # Center the view
        self.view.centerOn(data["center"][0], data["center"][1])

        # Set the zoom
        self.view.scale(1.0/self.view.zoomed, 1.0/self.view.zoomed)
        self.view.scale(data["zoom"], data["zoom"])
        self.view.zoomed = data["zoom"]

        # Add every widget in the data
        for widget in data["widgets"]:
            # ObjectTypes can't be converted to JSON
            # See the save method
            for item_type in registry.get_items():
                if widget["class"] == item_type.get_name():
                    self.add(item_type(widget["props"]), widget["pos"])
                    break

    # Method to save current layout to file
    def save(self):
        # General structure for saving the dashboard info
        data = {"zoom": self.view.zoomed, "center": [], "widgets": []}

        # Save the coordinates of the center of the view on the scene
        scene_center = self.view.mapToScene(self.view.width()/2, self.view.height()/2)
        data["center"] = [scene_center.x(), scene_center.y()]

        for items in self.widgets.values():
            # Get the proxy widget and dashitem
            proxy = items[0]
            dashitem = items[1]

            # Get the coordinates of the proxy widget on the scene
            scenepos = proxy.scenePos()

            # Add the position, dashitem name and dashitem props
            for item_type in registry.get_items():
                if type(dashitem) == item_type:
                    data["widgets"].append({"class": item_type.get_name(),
                                            "props": dashitem.get_props(),
                                            "pos": [scenepos.x(), scenepos.y()]})
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
        for menu_item in self.lockableActions:
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
        for menu_item in self.lockableActions:
            menu_item.setEnabled(True)

        # Enable selecting and moving plots
        for rect in self.widgets:
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=True)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=True)

    # Method to display help box
    # Yes it's jank deal with it
    def help(self):
        message = """
            WELCOME TO THE OMNIBUS DASHBOARD!

            Here are some useful navigation tips:

            - Regular scrolling moves stuff up and down
            - Shift + scrolling moves stuff left and right
                    - This sucks rn so use click and drag
                    - Someone fix it
            - Control/CMD + scrolling zooms in and out
            - Control/CMD + "=" or "-" also zooms in and out
            - Control/CMD + 0 resets the view to the middle
        """
        help_box = ConfirmDialog("Omnibus Help", message)
        help_box.exec()

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
                    self.view.zoom(200)
                case Qt.Key_Minus:
                    self.view.zoom(-200)
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

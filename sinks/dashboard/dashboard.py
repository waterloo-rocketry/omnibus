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
    QGraphicsRectItem,
    QFileDialog,
    QSplitter,
    QInputDialog,
    QMessageBox
)
from pyqtgraph.parametertree import ParameterTree
from items import registry
from omnibus.util import TickCounter
from utils import ConfirmDialog, EventTracker
# These need to be imported to be added to the registry
from items.plot_dash_item import PlotDashItem
from items.dynamic_text import DynamicTextItem
from items.periodic_can_sender import PeriodicCanSender
from items.gauge_item import GaugeItem
from items.image_dash_item import ImageDashItem
from items.text_dash_item import TextDashItem
from items.can_sender import CanSender
from items.plot_3D_orientation import Orientation3DDashItem
from items.plot_3D_position import Position3DDashItem
from items.table_view import TableViewItem
from publisher import publisher
from typing import Union

from omnibus import Sender

sender = Sender()


class QGraphicsViewWrapper(QGraphicsView):
    """
    Creating a QGraphicsView wrapper to intercept wheelEvents for UI enhancements.
    For example, we want to allow horizontal scrolling with a mouse, which we define
    as scrolling with a mouse while pressing the shift key.
    """

    def __init__(self, scene):
        super().__init__(scene)  # initialize the super class
        self.zoomed = 1.0
        self.SCROLL_SENSITIVITY = 1/3  # scale down the scrolling sensitivity

    def wheelEvent(self, event):
        """
        Zoom in/out if ctrl/cmd is held
        Scroll horizontally if shift is held
        Scroll vertically otherwise
        """
        angle = event.angleDelta()
        if event.modifiers() == Qt.ControlModifier:
            self.zoom(angle.y())
        elif event.source() == Qt.MouseEventNotSynthesized:  # event comes from a mouse
            if event.modifiers() == Qt.ShiftModifier:
                # determining the scrolling orientation based on the larger x/y component value
                absolute_angle = angle.x() if abs(angle.x()) > abs(angle.y()) else angle.y()
                numDegrees = absolute_angle * self.SCROLL_SENSITIVITY
                value = self.horizontalScrollBar().value()
                self.horizontalScrollBar().setValue(int(value + numDegrees))
            else:
                numDegrees = angle.y() * self.SCROLL_SENSITIVITY
                value = self.verticalScrollBar().value()
                self.verticalScrollBar().setValue(int(value + numDegrees))
        else:  # let the default implementation occur for everything else
            super().wheelEvent(event)

    # we define a function for zooming since keyboard zooming needs a function
    def zoom(self, angle: int):
        zoomFactor = 1 + angle*0.001  # create adjusted zoom factor
        self.zoomed *= zoomFactor  # needed to reset zoom
        self.scale(zoomFactor, zoomFactor)  # scale the scene

# Custom Dashboard class derived from QWidget


class Dashboard(QWidget):
    def __init__(self, callback):
        # Initialize the super class
        super().__init__()

        self.current_parsley_instances = []

        self.refresh_track = False

        publisher.subscribe("ALL", self.every_second)

        # Stores the selected parsley instance
        self.parsley_instance = "None"
        publisher.subscribe('outgoing_can_messages', self.send_can_message)

        # Called every frame to get new data
        self.callback = callback

        # Dictionary to map rectitems to widgets and dashitems
        self.widgets = {}

        # Keep track of if editing is allowed
        self.locked = False

        # The file from which the dashboard is loaded
        self.filename = "savefile.json"

        # Create a GUI
        self.width = 1100
        self.height = 700
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(self.width, self.height)

        # Create a large scene underneath the view
        self.scene = QGraphicsScene(0, 0, self.width*100, self.height*100)
        self.scene.selectionChanged.connect(self.on_selection_changed)

        # Create a layout manager
        self.layout = QVBoxLayout()
        # We wrap everything in a splitter view so that
        # we can resize the peremeter tree
        self.splitter = QSplitter(Qt.Horizontal)
        self.layout.addWidget(self.splitter)

        # Create a menubar for actions
        menubar = QMenuBar(self)

        # List to keep track of menu bar action that
        # can be disabled when dashboard is locked
        self.lockableActions = []

        # Add an action to the menu bar containing Save, Save As and Open.
        # Save will save the layout of the dashboard
        # Save As will prompt a name, then saves the layout of the dashboard
        # Open loads the layout of the dashboard
        add_file_menu = menubar.addMenu("File")

        file_save_layout_action = add_file_menu.addAction("Save")
        file_save_layout_action.triggered.connect(self.save)

        file_save_as_layout_action = add_file_menu.addAction("Save As")
        file_save_as_layout_action.triggered.connect(self.save_as)

        file_open_layout_action = add_file_menu.addAction("Open")
        file_open_layout_action.triggered.connect(self.open)

        self.lockableActions.append(file_save_layout_action)
        self.lockableActions.append(file_save_as_layout_action)
        self.lockableActions.append(file_open_layout_action)

        # Create a sub menu which will be used
        # to add items to our dash board.
        # For all dash items we support, there will
        # be a corresponding action to add that item
        add_item_menu = menubar.addMenu("Add Item")

        # Need to create triggers like this
        # because of the way python handles
        def create_registry_trigger(i):
            def return_fun():
                if not self.locked:
                    self.add(registry.get_items()[i](self.on_item_resize))
            return return_fun

        for i in range(len(registry.get_items())):
            new_action = add_item_menu.addAction(registry.get_items()[i].get_name())
            new_action.triggered.connect(create_registry_trigger(i))
            self.lockableActions.append(new_action)

        # adding a button to the dashboard that removes all dashitems on the screen
        remove_dashitems = menubar.addMenu("Clear")
        remove_dashitems_action = remove_dashitems.addAction("Remove all the dashitems")
        remove_dashitems_action.triggered.connect(self.remove_all)
        self.lockableActions.append(remove_dashitems_action)

        # adding a button to switch instances of parsley
        self.can_selector = menubar.addMenu("Parsley")

        # Add an action to the menu bar to lock/unlock
        # the dashboard
        add_lock_menu = menubar.addMenu("Lock")
        lock_action = add_lock_menu.addAction("Lock Dashboard")
        lock_action.triggered.connect(self.lock)
        self.lockableActions.append(lock_action)
        unlock_action = add_lock_menu.addAction("Unlock Dashboard")
        unlock_action.triggered.connect(self.unlock)

        # An action to the to the menu bar to duplicate
        # the selected item
        duplicate_item_menu = menubar.addMenu("Duplicate")
        duplicate_action = duplicate_item_menu.addAction("Duplicate Item")
        duplicate_action.triggered.connect(self.on_duplicate)
        self.lockableActions.append(duplicate_action)

        # Add an action to the menu bar to display a
        # help box
        add_help_menu = menubar.addMenu("Help")
        help_action = add_help_menu.addAction("Omnibus Help")
        help_action.triggered.connect(self.help)

        self.layout.setMenuBar(menubar)

        # Set the counter
        self.counter = TickCounter(1)

        # Create the view and add it to the widget
        self.view = QGraphicsViewWrapper(self.scene)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setRenderHints(QPainter.Antialiasing)
        # zooms to the position of mouse
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.view.viewport().setAttribute(Qt.WidgetAttribute.WA_AcceptTouchEvents, False)
        self.splitter.addWidget(self.view)
        self.parameter_tree_placeholder = ParameterTree()
        self.parameter_tree_placeholder.hide()
        self.splitter.addWidget(self.parameter_tree_placeholder)

        # This makes both the scene and the parameter tree
        # non collapsible. This is important because otherwise
        # the widgets can go to width 0 and it hard to get them back
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.setLayout(self.layout)

        # enable certain keyboard shortcuts
        self.key_press_signals = EventTracker()
        self.key_press_signals.zoom_in.connect(lambda: self.view.zoom(200))
        self.key_press_signals.zoom_out.connect(lambda: self.view.zoom(-200))
        self.key_press_signals.zoom_reset.connect(self.reset_zoom)
        self.key_press_signals.backspace_pressed.connect(self.remove_selected)
        self.installEventFilter(self.key_press_signals)

    def select_instance(self, name):
        self.parsley_instance = name
        self.refresh_track = True

    def every_second(self, payload, stream):
        def on_select(string):
            def retval():
                self.select_instance(string)
            return retval

        parsley_streams = [e[15:]
                           for e in publisher.get_all_streams() if e.startswith("Parsley health")]

        parsley_streams.append("None")

        if self.current_parsley_instances != parsley_streams or self.refresh_track:
            self.can_selector.clear()

            if self.refresh_track:
                self.refresh_track = False

            self.current_parsley_instances = parsley_streams

            for inst in range(len(parsley_streams)):
                new_action = self.can_selector.addAction(parsley_streams[inst])
                new_action.triggered.connect(on_select(parsley_streams[inst]))
                new_action.setCheckable(True)

                if self.parsley_instance == parsley_streams[inst]:
                    new_action.setChecked(True)
                else:
                    new_action.setChecked(False)

                self.lockableActions.append(new_action)

    def send_can_message(self, stream, payload):
        payload['parsley'] = self.parsley_instance
        sender.send("CAN/Commands", payload)

    # Method to open the parameter tree to the selected item

    def on_selection_changed(self):
        items = self.scene.selectedItems()
        if len(items) != 1:
            self.splitter.replaceWidget(1, self.parameter_tree_placeholder)
            self.parameter_tree_placeholder.hide()
            return
        # Show the tree
        item = self.widgets[items[0]][1]
        if self.splitter.widget(1) is not item.parameter_tree:
            self.splitter.replaceWidget(1, item.parameter_tree)
        item.parameter_tree.show()

        # subtract 100 for some padding, these sizes are relative
        total_width = self.splitter.size().width() - 100
        tree_width = item.parameter_tree.sizeHint().width()
        self.splitter.setSizes([total_width - tree_width, tree_width])

    def on_duplicate(self):
        selected_items = self.scene.selectedItems()

        if len(selected_items) != 1:
            pass  # maybe do something better

        rect = selected_items[0]

        for candidate, (proxy, item) in self.widgets.items():
            if rect is candidate:
                scenepos = proxy.scenePos()
                viewpos = self.view.mapFromScene(scenepos)

                params = item.get_serialized_parameters()

                self.add(type(item)(self.on_item_resize, params),
                         (viewpos.x() + 20, viewpos.y() + 20))

                break

    # method to handle dimension changes in parameter tree

    def on_item_resize(self, item):
        width = item.parameters.param('width').value() + 1
        height = item.parameters.param('height').value() + 1
        for proxy, candidate in self.widgets.values():
            if candidate is item:
                pos = proxy.pos()
                proxy.parentItem().setRect(pos.x(), pos.y(), width, height)
                return

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

            mapped = self.view.mapToScene(int(view_xpos), int(view_ypos))

            # Center the widget in the view. Qt sets position
            # based on the upper left corner, so subtract
            # half the width and height of the widget to
            # center the center
            xpos = mapped.x() - (width/2)
            ypos = mapped.y() - (height/2)

        proxy.setPos(xpos, ypos)

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
        if not os.path.exists(self.filename):
            return

        with open(self.filename, "r") as savefile:
            data = json.load(savefile)

        # Set the zoom
        curr_zoom = self.view.zoomed
        self.view.scale(1/curr_zoom, 1/curr_zoom)
        new_zoom = data["zoom"]
        self.view.scale(new_zoom, new_zoom)
        self.view.zoomed = new_zoom

        # Add every widget in the data
        for widget in data["widgets"]:
            # ObjectTypes can't be converted to JSON
            # See the save method
            for item_type in registry.get_items():
                if widget["class"] == item_type.get_name():
                    self.add(item_type(self.on_item_resize, widget["params"]), widget["pos"])
                    break

    # Method to save current layout to file
    def save(self, filename: Union[str, bool] = False):
        save_directory = "saved-files"

         # Ensure the save directory exists, if not, create it
        if not os.path.exists(save_directory):
            os.makedirs(save_directory)

        # If file name doesn't exist, default name is savefile.json
        if filename is False:
            filename = self.filename

        # Adjust filename to include the save directory
        filename = os.path.join(save_directory, os.path.basename(filename))

        # General structure for saving the dashboard info
        data = {"zoom": self.view.zoomed, "center": [], "widgets": []}

        # Save the coordinates of the center of the view on the scene
        scene_center = self.view.mapToScene(self.view.width()//2, self.view.height()//2)
        data["center"] = [scene_center.x(), scene_center.y()]

        for items in self.widgets.values():
            # Get the proxy widget and dashitem
            proxy = items[0]
            dashitem = items[1]

            # Get the coordinates of the proxy widget on the view
            scenepos = proxy.scenePos()
            viewpos = self.view.mapFromScene(scenepos)

            # Add the position, dashitem name and dashitem props
            for item_type in registry.get_items():
                if type(dashitem) == item_type:
                    data["widgets"].append({"class": item_type.get_name(),
                                            "params": dashitem.get_serialized_parameters(),
                                            "pos": [viewpos.x(), viewpos.y()]})
                    break

        with open(filename, "w") as savefile:
            json.dump(data, savefile)

    # Method to save file with a custom chosen name
    def save_as(self):
        user_response = self.show_save_as_prompt()
        self.save(user_response)

    # Method to allow user to choose name of the file of the configuration they would like to save
    def show_save_as_prompt(self) -> str:
        # Show a prompt box using QInputDialog
        text, ok = QInputDialog.getText(self, 'Input Dialog', 'Enter file name without extension:')
        
        # Check if OK was pressed and text is not empty
        if ok and text:
            return text + ".json"
        elif ok:
            QMessageBox.warning(self, 'Warning', 'No input provided, try again')

    # Method to switch to a layout in a different file
    def open(self):
        (filename, _) = QFileDialog.getOpenFileName(self, "Open File", "", "JSON Files (*.json)")

        if not filename:
            return
        
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

    # Method to handle exit
    def closeEvent(self, event):
        self.remove_all()

    # Method to display help box
    def help(self):
        message = """
            WELCOME TO THE OMNIBUS DASHBOARD!

            Here are some useful navigation tips:

            - Regular scrolling moves stuff vertically
            - Shift + scrolling moves stuff horizontally
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
    def reset_zoom(self):
        # Reset the zoom
        self.view.scale(1/self.view.zoomed, 1/self.view.zoomed)
        self.view.zoomed = 1

        # Center the view
        scene_width = self.scene.width()
        scene_height = self.scene.height()
        self.view.centerOn(scene_width/2, scene_height/2)

    def remove_selected(self):
        if self.locked:
            return
        for item in self.scene.selectedItems():
            self.remove(item)
            self.widgets.pop(item)


# Function to launch the dashboard
def dashboard_driver(callback):
    # quit applicaiton from terminal
    signal.signal(signal.SIGINT, lambda *args: QApplication.quit())
    app = QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.update()
    dash.show()
    dash.load()
    app.exec()

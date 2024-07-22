from enum import Enum
import os
import sys
import json
import signal

import pyqtgraph
from pyqtgraph.Qt.QtCore import Qt, QTimer
from pyqtgraph.Qt.QtGui import QPainter, QAction
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
    QMessageBox,
    QDialog,
    QLabel,
    QCheckBox,
    QHBoxLayout,
    QPushButton,
    QGraphicsProxyWidget
)
from pyqtgraph.parametertree import ParameterTree
from items import registry
from omnibus.util import TickCounter
from utils import ConfirmDialog, EventTracker
from publisher import publisher
from typing import Optional
from omnibus import Sender
from items.dashboard_item import DashboardItem

# These need to be imported to be added to the registry
from items.plot_dash_item import PlotDashItem
from items.gauge_item import GaugeItem
from items.progress_bar import ProgressBarItem
from items.image_dash_item import ImageDashItem
from items.text_dash_item import TextDashItem
from items.dynamic_text import DynamicTextItem
from items.periodic_can_sender import PeriodicCanSender
from items.can_sender import CanSender
from items.standard_display_item import StandardDisplayItem


pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')


class QGraphicsViewWrapper(QGraphicsView):
    """
    Creating a QGraphicsView wrapper to intercept wheelEvents for UI enhancements.
    For example, we want to allow horizontal scrolling with a mouse, which we define
    as scrolling with a mouse while pressing the shift key.
    """

    def __init__(self, scene, dashboard):
        super().__init__(scene)  # initialize the super class
        self.zoomed = 1.0
        self.SCROLL_SENSITIVITY = 1/3  # scale down the scrolling sensitivity
        self.dashboard = dashboard
        
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
    
    # override the mouseDoubleClickEvent to open the property panel
    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.pos())
        # if an item is clicked, open the property panel of item
        if item in self.scene().items():
            self.dashboard.open_property_panel(item)
        else:
            #else close the property panel
            self.dashboard.open_property_panel(None)
        super().mouseDoubleClickEvent(event)  # Call the superclass implementation
    
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

        self.omnibus_sender = Sender()
        self.current_parsley_instances = []
        self.refresh_track = False

        publisher.subscribe("ALL", self.every_second)

        # Stores the selected parsley instance
        self.parsley_instance = "None"
        publisher.subscribe('outgoing_can_messages', self.send_can_message)

        # Called every frame to get new data
        self.callback = callback

        # Dictionary to map rectitems to widgets and dashitems
        self.widgets: dict[QGraphicsRectItem, tuple[QGraphicsProxyWidget, DashboardItem]] = {}

        # Keep track of if editing is allowed
        self.locked = False

        # Determine the specific directory you want to always open
        script_dir = os.path.dirname(os.path.abspath(__file__))
        self.save_directory = os.path.join(script_dir, "..", "..", "sinks", "dashboard", "saved-files")
        
        # The file from which the dashboard is loaded
        self.file_location = os.path.join(self.save_directory, "savefile.json")

        # Keep track on whether the save popup should be shown on exit.
        self.should_show_save_popup = True
        
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

        file_save_layout_action = add_file_menu.addAction("Save (^s)")
        file_save_layout_action.triggered.connect(self.save)

        file_save_as_layout_action = add_file_menu.addAction("Save As (^S)")
        file_save_as_layout_action.triggered.connect(self.save_as)

        file_open_layout_action = add_file_menu.addAction("Open (^o)")
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
                    self.add(registry.get_items()[i](self))
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
        lock_action = add_lock_menu.addAction("Lock Dashboard (^l)")
        lock_action.triggered.connect(self.lock)
        self.lockableActions.append(lock_action)
        unlock_action = add_lock_menu.addAction("Unlock Dashboard (^l)")
        unlock_action.triggered.connect(self.unlock)
        lock_selected = add_lock_menu.addAction("Lock Selected (l)")
        lock_selected.triggered.connect(self.lock_selected)
        self.lockableActions.append(lock_selected)
        self.unlock_items_menu = add_lock_menu.addMenu("Unlock Items")
        """Menu containing actions to unlock items that are locked, in the order
        in which they were locked.
        """
        self.locked_widgets: list[tuple[QGraphicsRectItem, QAction]] = []
        """List of items which are locked, in the order in which they
        were locked.
        
        Includes the rect item and the unlock action."""

        # An action to the to the menu bar to duplicate
        # the selected item
        duplicate_item_menu = menubar.addMenu("Duplicate")
        duplicate_action = duplicate_item_menu.addAction("Duplicate Item (^d)")
        duplicate_action.triggered.connect(self.on_duplicate)
        self.lockableActions.append(duplicate_action)

        # We have a menu in the top to allow users to change the stacking order
        # of the selected items.
        order_menu = menubar.addMenu("Order")
        send_to_front_action = order_menu.addAction("Send to Front (^])")
        send_to_front_action.triggered.connect(self.send_to_front)
        self.lockableActions.append(send_to_front_action)
        send_to_back_action = order_menu.addAction("Send to Back (^[)")
        send_to_back_action.triggered.connect(self.send_to_back)
        self.lockableActions.append(send_to_back_action)
        send_forward_action = order_menu.addAction("Send Forward (])")
        send_forward_action.triggered.connect(self.send_forward)
        self.lockableActions.append(send_forward_action)
        send_backward_action = order_menu.addAction("Send Backward ([)")
        send_backward_action.triggered.connect(self.send_backward)
        self.lockableActions.append(send_backward_action)

        # Add an action to the menu bar to display a
        # help box
        add_help_menu = menubar.addMenu("Help")
        help_action = add_help_menu.addAction("Omnibus Help")
        help_action.triggered.connect(self.help)

        self.layout.setMenuBar(menubar)

        # Set the counter
        self.counter = TickCounter(1)

        # Create the view and add it to the widget
        self.view = QGraphicsViewWrapper(self.scene, self)
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
        self.key_press_signals.save_file_keys_pressed.connect(self.save)
        self.key_press_signals.save_as_file_keys_pressed.connect(self.save_as)
        self.key_press_signals.open_file_keys_pressed.connect(self.open)
        self.key_press_signals.duplicate.connect(self.on_duplicate)
        self.key_press_signals.lock_dashboard.connect(self.toggle_lock)
        self.key_press_signals.lock_selected.connect(self.lock_selected)
        self.key_press_signals.send_forward.connect(self.send_forward)
        self.key_press_signals.send_backward.connect(self.send_backward)
        self.key_press_signals.send_to_front.connect(self.send_to_front)
        self.key_press_signals.send_to_back.connect(self.send_to_back)
        self.installEventFilter(self.key_press_signals)
        
        # Data used to check unsaved changes and indicate on the window title
        self.current_data = self.get_data()["widgets"]
        self.unsave_indicator = False
        
        # For every 5 second, check if there are any changes
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.change_detector)
        self.timer.start(100)  # Check every 0.1 seconds

        QApplication.setStyle('Fusion')

    def select_instance(self, name):
        self.parsley_instance = name
        self.refresh_track = True

    def check_for_changes(self):
        if self.unsave_indicator:
            return True
        elif (self.current_data != self.get_data()["widgets"]):
            self.unsave_indicator = True
            return True
        return False

    def change_detector(self):
        title_string = "Omnibus Dashboard - "
        
        title_string += os.path.basename(self.file_location)
            
        if self.check_for_changes():
            title_string += " ⏺"

        self.setWindowTitle(title_string)

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
        self.omnibus_sender.send("CAN/Commands", payload)

    # Method to open the parameter tree to the selected item
    def open_property_panel(self, item):
        items = self.scene.selectedItems()

        if len(items) == 0:
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


    # On selection changed, hide the parameter tree
    def on_selection_changed(self):
        current_widget = self.splitter.widget(1)
        if current_widget is not self.parameter_tree_placeholder:
            self.splitter.replaceWidget(1, self.parameter_tree_placeholder)
            self.parameter_tree_placeholder.hide()


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

                self.add(type(item)(self, params),
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
    def add(self, dashitem, pos=None) -> QGraphicsRectItem:
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

        return rect

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
        if not os.path.exists(self.file_location) or os.stat(self.file_location).st_size == 0:
            return

        with open(self.file_location, "r") as savefile:
            data = json.load(savefile)

        # Set the zoom
        curr_zoom = self.view.zoomed
        self.view.scale(1/curr_zoom, 1/curr_zoom)
        new_zoom = data["zoom"]
        self.view.scale(new_zoom, new_zoom)
        self.view.zoomed = new_zoom
        # Capture the save on exit settting.
        if "should_show_save_popup" in data and not data["should_show_save_popup"]:
            self.should_show_save_popup = False    

        locked_item_pairs = []

        # Add every widget in the data
        for widget in data["widgets"]:
            # ObjectTypes can't be converted to JSON
            # See the save method
            for item_type in registry.get_items():
                if widget["class"] == item_type.get_name():
                    item = item_type(self, widget["params"])
                    rect = self.add(item, widget["pos"])
                    if "locked" in widget and widget["locked"] is not None:
                        locked_item_pairs.append((widget["locked"], rect))
                    break

        locked_item_pairs.sort(key=lambda pair: pair[0])
        for _index, rect in locked_item_pairs:
            self.lock_widget(rect)

        self.current_data = data["widgets"]
        self.unsave_indicator = False

        self.change_detector()

    # Method to save current layout to file
    def save(self):
        data = self.get_data()
        
        self.current_data = data["widgets"]
        self.unsave_indicator = False
                    
        # Write data to savefile
        os.makedirs(os.path.dirname(self.file_location), exist_ok=True)
        with open(self.file_location, "w") as savefile:
            json.dump(data, savefile)

        self.change_detector()

    # Method to save file with a custom chosen name
    def save_as(self):
        self.file_location = os.path.join(self.save_directory, self.show_save_as_prompt())
        self.save()

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
        # Ensure the save directory exists, if not, create it
        if not os.path.exists(self.save_directory):
            os.makedirs(self.save_directory)
            
        (filename, _) = QFileDialog.getOpenFileName(self, "Open File", self.save_directory, "JSON Files (*.json)")

        # If the user presses cancel, do nothing
        if not filename:
            return
        
        self.file_location = filename
        self.load()
        
        self.change_detector()

    # Method to lock dashboard
    def lock(self):
        self.locked = True
        self.setWindowTitle("Omnibus Dashboard - LOCKED")

        # Disable menu actions
        for menu_item in self.lockableActions:
            menu_item.setEnabled(False)

        for _rect, action in self.locked_widgets:
            action.setEnabled(False)

        # Disable selecting and moving plots
        for rect in self.widgets:
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=False)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
        
        self.scene.clearSelection()
        
    def toggle_lock(self):
        """Toggle lock/unlock state of the dashboard"""
        if self.locked:
            self.unlock()
        else:
            self.lock()

    # Method to unlock dashboard
    def unlock(self):
        self.locked = False
        self.setWindowTitle("Omnibus Dashboard")

        # Enable menu actions
        for menu_item in self.lockableActions:
            menu_item.setEnabled(True)
            
        for _rect, action in self.locked_widgets:
            action.setEnabled(True)

        # Enable selecting and moving plots
        for rect in self.widgets:
            individually_locked = any(rect == pair[0] for pair in self.locked_widgets)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=not individually_locked)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=not individually_locked)
            
    def lock_widget(self, rect: QGraphicsRectItem):
        """Mark a widget rect as locked."""
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=False)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=False)
        name = self.widgets[rect][1].get_name()
        action = self.unlock_items_menu.addAction(f"Unlock {name}")

        def unlock():
            self.locked_widgets = [pair for pair in self.locked_widgets if pair[0] != rect]
            self.unlock_items_menu.removeAction(action)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, enabled=not self.locked)
            rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, enabled=not self.locked)
            
        action.triggered.connect(unlock)
        self.locked_widgets.append((rect, action))

        self.scene.clearSelection()

    def lock_selected(self):
        """Mark all selected widgets as locked, in an arbitrary order"""
        for widget in self.scene.selectedItems():
            self.lock_widget(widget)

    # Method to handle exit
    def closeEvent(self, event):
        # Get data from savefile.
        if os.path.exists(self.file_location) and os.stat(self.file_location).st_size != 0:
            with open(self.file_location, "r") as savefile:
                old_data = json.load(savefile)
        else:
            # Set default values to default data.
            old_data = {"zoom": self.view.zoomed, "center": [], "widgets": [], "should_show_save_popup": True}
        
        # Obtain current data 
        new_data = self.get_data()
        # Automatically exit if user has clicked "Dont ask again checkbox" or no new changes are made.
        if not self.should_show_save_popup or new_data["widgets"] == old_data["widgets"]:
            self.remove_all()
        else:
            # Execute save popup dialog.
            self.show_save_popup(old_data, event)


    # Method to retrieve current data on dashboard.
    def get_data(self):
        # General structure for obtaining the dashboard info
        data = {"zoom": self.view.zoomed, "center": [], "widgets": [], "should_show_save_popup": True}

        # Obtain current save on exit value.
        data["should_show_save_popup"] = self.should_show_save_popup
    
        # Capture the coordinates of the center of the view on the scene
        scene_center = self.view.mapToScene(self.view.width()//2, self.view.height()//2)
        data["center"] = [scene_center.x(), scene_center.y()]

        # We follow the scene stacking order to serialize dashitems.
        # We find all relevant proxy widgets and look up their
        # corresponding dashitems.
        for rect in self.scene.items(Qt.SortOrder.AscendingOrder):
            if not isinstance(rect, QGraphicsRectItem):
                continue
            items = self.widgets[rect]
            proxy = items[0]
            dashitem = items[1]

            # Get the coordinates of the proxy widget on the view
            scenepos = proxy.scenePos()
            viewpos = self.view.mapFromScene(scenepos)

            # Add the position, dashitem name and dashitem props
            for item_type in registry.get_items():
                if type(dashitem) == item_type:
                    locked_index = next((i for i, (candidate, _action) in enumerate(self.locked_widgets) if candidate == rect), None)
                    data["widgets"].append({"class": item_type.get_name(),
                                            "params": dashitem.get_serialized_parameters(),
                                            "pos": [viewpos.x(), viewpos.y()],
                                            "locked": locked_index})
        
        return data
    
    # Method to display save on exit popup.
    def show_save_popup(self, old_data, event):
        # Display Popup that prompts for save.
        popup = QDialog()
        popup.setWindowTitle('Save Work')
        popup.setModal(True)

        save_layout = QVBoxLayout()
        # Add UI Components to Popup.
        label = QLabel("You have made changes, would you like to save them")
        save_layout.addWidget(label)
        # Add a checkbox
        dont_ask_again_checkbox = QCheckBox("Don't ask again")
        save_layout.addWidget(dont_ask_again_checkbox)

        # Create horizontal button layout and add buttons
        button_layout = QHBoxLayout()
        save_changes = QPushButton("Yes")
        discard_changes = QPushButton("No")
        cancel = QPushButton("Cancel")

        button_layout.addWidget(save_changes)
        button_layout.addWidget(discard_changes)
        button_layout.addWidget(cancel)
        # Apply layout to save popup
        save_layout.addLayout(button_layout)
        popup.setLayout(save_layout)

        class Event(Enum):
            SAVE_CHANGES = 1
            DISCARD_CHANGES = 2
            CANCEL = 3
        # Connect buttons to action listeners. 
        save_changes.clicked.connect(lambda: popup.done(Event.SAVE_CHANGES.value))
        discard_changes.clicked.connect(lambda: popup.done(Event.DISCARD_CHANGES.value))
        cancel.clicked.connect(lambda: popup.done(Event.CANCEL.value))

        result = popup.exec_()

        if dont_ask_again_checkbox.isChecked():
            self.should_show_save_popup = False
        
        if result == Event.SAVE_CHANGES.value:
            self.save()
            self.remove_all()
        elif result == Event.DISCARD_CHANGES.value:
            if not self.should_show_save_popup:
                # Persist old data to JSON file.
                old_data["should_show_save_popup"] = False
                with open(self.file_location, "w") as savefile:
                    json.dump(old_data, savefile)
            self.remove_all()
        else:
            event.ignore()


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

            Keyboard shortcuts:
            - Ctrl+S - Save
            - Ctrl+Shift+S - Save As
            - Ctrl+O - Open
            - Ctrl+L - Toggle Lock the Dashboard
            - L - Lock Selected
            - Ctrl+D - Duplicate Item
            - Ctrl+] - Send to Front
            - Ctrl+[ - Send to Back
            - ] - Send Forward
            - [ - Send Backward
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

    def send_to_front(self):
        """Send the selected items to the front of the stacking order.
        If there are multiple items selected, they will maintain their relative
        order.
        """
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 0:
            return
        
        order_of_items = {}
        for i, item in enumerate(self.scene.items(Qt.SortOrder.AscendingOrder)):
            order_of_items[item] = i
        for item in sorted(selected_items, key=lambda item: order_of_items[item]):
            self.scene.removeItem(item)
            self.scene.addItem(item)

    def send_to_back(self):
        """Send the selected item to the back of the stacking order.
        If there are multiple items selected, they will maintain their relative
        order."""
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 0:
            return
        
        # For some reason QGraphicsItem::stackBefore doesn't work, so we just
        # go with manually adding/removing all the items that are not supposed
        # to be at the back
        readd_items = [item for item in self.scene.items(Qt.SortOrder.AscendingOrder)
                        if isinstance(item, QGraphicsRectItem) and item not in selected_items]
        for item in readd_items:
            self.scene.removeItem(item)
            self.scene.addItem(item)

    def send_forward(self):
        """Send the selected item one layer forward in the stacking order,
        if possible. If there are multiple items selected, we will try to apply
        this operation to each from front to back, but we will not apply the
        operation if the next forward item is also selected.
        """
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 0:
            return
        
        # Too complicated to figure out what to add and remove. Just do it for
        # all in a virtual array first
        items = [item for item in self.scene.items(Qt.SortOrder.AscendingOrder)
                    if isinstance(item, QGraphicsRectItem)]
        for item in items:
            self.scene.removeItem(item)
        for i in reversed(range(len(items) - 1)):
            if items[i] in selected_items and items[i + 1] not in selected_items:
                tmp = items[i]
                items[i] = items[i + 1]
                items[i + 1] = tmp
        for item in items:
            self.scene.addItem(item)

    def send_backward(self):
        """Send the selected item one layer backward in the stacking order,
        if possible. If there are multiple items selected, we will try to apply
        this operation to each from back to front, but we will not apply the
        operation if the next backward item is also selected.
        """
        selected_items = self.scene.selectedItems()
        if len(selected_items) == 0:
            return
        
        items = [item for item in self.scene.items(Qt.SortOrder.AscendingOrder)
                    if isinstance(item, QGraphicsRectItem)]
        for item in items:
            self.scene.removeItem(item)
        for i in range(1, len(items)):
            if items[i] in selected_items and items[i - 1] not in selected_items:
                tmp = items[i]
                items[i] = items[i - 1]
                items[i - 1] = tmp
        for item in items:
            self.scene.addItem(item)

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
    dash.load() # This will default load the savefile.json if it exists
    app.exec()

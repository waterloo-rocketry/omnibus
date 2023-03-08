import os, sys, json
from time import sleep

from pyqtgraph.Qt.QtCore import Qt, QTimer, QPoint
from pyqtgraph.Qt.QtWidgets import (
    QGraphicsView,
    QGraphicsScene,
    QApplication,
    QWidget,
    QMenuBar,
    QVBoxLayout,
    QGraphicsItem,
    QGraphicsRectItem,
    QPushButton
)

from items import registry
from items.plot_dash_item import PlotDashItem
from items.can_message_table import CanMsgTableDashItem
from omnibus.util import TickCounter
from utils import prompt_user

class MyQGraphicsView(QGraphicsView):

    def __init__ (self, parent=None):
        super(MyQGraphicsView, self).__init__ (parent)
        self.zoom = False

    def wheelEvent(self, event):
        print(self.zoom)
        if self.zoom:
            print("I'm in")
            # Zoom Factor
            zoomInFactor = 1.1
            zoomOutFactor = 1 / zoomInFactor

            # Set Anchors
            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

            # Zoom
            angle = event.angleDelta().y()
            if angle > 0:
                zoomFactor = zoomInFactor
            elif angle < 0:
                zoomFactor = zoomOutFactor
            else:
                zoomFactor = 1

            self.scale(zoomFactor, zoomFactor)
            print("Scaled")
 
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Shift: 
            print("Pressed")
            self.zoom =  True

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Shift:
            print("Released")
            self.zoom = False


class Dashboard(QWidget):
    def __init__(self, callback):
        # Initialize the super class
        super().__init__()

        # Called every frame to get new data
        self.callback = callback 

        # List to keep track of widgets
        self.widgets = {}

        # The file from which the dashboard is loaded
        self.filename = "savefile.json"
        self.filename_cache = [self.filename]

        # Create a GUI
        self.scene = QGraphicsScene(0,0,2000,1500)
        self.setWindowTitle("Omnibus Dashboard")
        self.resize(1100, 700)

        # Create a grid layout
        self.layout = QVBoxLayout()

        # Create a menubar for actions
        menubar = QMenuBar(self)

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

        # Add a button to remove the selected widget
        remove = QPushButton("Remove Selected Widget")
        remove.clicked.connect(self.remove)
        self.layout.addWidget(remove)

        # Load the last saved state
        self.load()

        # Set the counter
        self.counter = TickCounter(1)

        # Create the view and add it to the widget
        view = MyQGraphicsView(self.scene)
        view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.layout.addWidget(view)
        self.setLayout(self.layout)

    def add(self, dashitem):
        # Add the dash item to the scene and get
        # its proxy widget
        proxy = self.scene.addWidget(dashitem)
        height = proxy.size().height()
        width = proxy.size().width()
        
        # Create a rectangle around the proxy widget
        # to make it movable and selectable
        rect = QGraphicsRectItem(-1, -1, width+1, height+1)
        proxy.setParentItem(rect)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        rect.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable)
        self.scene.addItem(rect)
        self.widgets[rect] = [proxy, dashitem]

    def remove(self):
        for item in self.scene.selectedItems():
            components = self.widgets[item]
            proxy = components[0]
            dashitem = components[1]
            self.scene.removeItem(item)
            proxy.deleteLater()
            dashitem.on_delete()

    def load(self):
        # TODO
        pass

    def save(self):
        # TODO
        pass

    def switch(self):
        # TODO
        pass
        
    # called every frame
    def update(self):
        self.counter.tick()

        # Filter to 5 frames per update on analytics
        if not (self.counter.tick_count() % 5):
            fps = self.counter.tick_rate()

        self.callback()


def dashboard_driver(callback):
    app = QApplication(sys.argv)
    dash = Dashboard(callback)

    timer = QTimer()
    timer.timeout.connect(dash.update)
    timer.start(16)  # Capped at 60 Fps, 1000 ms / 16 ~= 60

    dash.show()
    app.exec()

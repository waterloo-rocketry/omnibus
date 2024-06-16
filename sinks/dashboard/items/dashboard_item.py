from pyqtgraph.Qt.QtWidgets import QWidget, QHeaderView
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import ActionParameter, ActionParameterItem
from collections import OrderedDict
from PySide6.QtGui import QPainter, QColor
from PySide6.QtCore import QRect
import json
from typing import Callable

from .no_text_action_parameter import NoTextActionParameter


class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    To create a new dashboard item, subclass this class and implement the following methods:
        - get_name() ;  just the name, has to be static
        - add_parameters() ; return a list of pyqtgraph Parameter objects specific to the widget
    """

    """Whether the dashboard item is locked, which disables selection"""

    def __init__(self, resize_callback, lock_item: Callable[['DashboardItem'], None], params=None):
        super().__init__()
        self.setMouseTracking(True)
        self.corner_grabbed = False
        self.corner_size = 20
        self.resize_callback = resize_callback
        self.lock_item = lock_item
        """
        We use pyqtgraph's ParameterTree functionality to make an easy interface for setting
        parameters. Subclasses should add their own parameters in their __init__ as follows:

        self.parameters.addChildren([
            { "name": ..., "type": ... },
            ...
        ])

        Subclasses should then set up their sigValueChanged listeners to properly respond to
        when parameters change, just like how we listen to the size values here:
        """
        self.parameters = Parameter.create(name=self.get_name(), type='group', children=[
            {"name": "width", "type": "int", "value": 100},
            {"name": "height", "type": "int", "value": 100}
        ])

        lock_parameter = NoTextActionParameter(name="lock")
        lock_parameter.sigActivated.connect(self.lock)
        self.parameters.addChild(lock_parameter)

        # add widget specific parameters
        self.parameters.addChildren(self.add_parameters())

        self.parameter_tree = ParameterTree(showHeader=True)
        self.parameter_tree.setParameters(self.parameters, showTop=False)
        self.parameter_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        # add listeners before restoring state so that the
        # dimensions are set correctly from the saved state
        self.parameters.child("width").sigValueChanged.connect(lambda _, val:
                                                               self.resize(
                                                                   val, self.size().height())
                                                               )
        self.parameters.child("height").sigValueChanged.connect(lambda _, val:
                                                                self.resize(
                                                                    self.size().width(), val)
                                                                )

        # restore state is params are provided
        if params:
            state = json.loads(params, object_pairs_hook=OrderedDict)
            self.parameters.restoreState(state, addChildren=False, removeChildren=False)

    def lock(self):
        """Set the dashboard item as locked.
        """
        self.lock_item(self)

    def resizeEvent(self, _):
        # These will trigger our lambdas above, but that's not an issue.
        self.parameters.child("width").setValue(self.size().width())
        self.parameters.child("height").setValue(self.size().height())
        self.resize_callback(self)

    def add_parameters(self) -> list[Parameter]:
        """
        This function is called when a dashitem is added to the screen. It should return a list
        of Parameter that are required to recreate the dashitem except for the dimensions.
        """
        return []

    @staticmethod
    def get_name():
        '''
        Return a nicer name for the Dash Item instead of the class name
        '''
        raise NotImplementedError

    def get_parameters(self) -> Parameter:
        """
        Returns an instance of a pyqtgraph Parameter which contains all the properties that this widget requires.
        """
        return self.parameters

    def get_serialized_parameters(self):
        """
        This function is called when a dashitem is saved to the config file. It should return a dictionary of
        properties that are required to recreate the dashitem.
        """
        return json.dumps(self.parameters.saveState(filter='user'))

    def on_delete(self):
        """
        This function is called when a dashitem is removed from the screen. In practice, this will likely be used to
        remove subscriptions from series
        """
        pass
    
    """
    The following functions are used to make the widget resizable by dragging the bottom right corner.
    """

    def mousePressEvent(self, event):
        """ Starts resizing the widget when the mouse is pressed in the bottom right corner.

        Notes:
            if the mouse is not in the bottom right corner, the event is passed to the base class method for normal processing.
        """
        if self.isInCorner(event.pos()):
            self.corner_grabbed = True
            self.grab_start_pos = event.globalPos()
            self.start_rect = self.rect()
        else:
            super().mousePressEvent(event)  # Call the base class method for normal processing

    def mouseMoveEvent(self, event):
        """ 
        Resizes the widget while the mouse is being moved.
        """
        if self.corner_grabbed:
            delta = event.globalPos() - self.grab_start_pos
            new_width = max(self.start_rect.width() + delta.x(), self.minimumWidth())
            new_height = max(self.start_rect.height() + delta.y(), self.minimumHeight())
            self.resize(new_width, new_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        self.drawCorner(painter)

    def mouseReleaseEvent(self, event):
        """ Stops resizing the widget when the mouse is released.

        Args:
            event (QMouseEvent): The mouse release event.
        """
        self.corner_grabbed = False

    def isInCorner(self, pos):
        return pos.x() > self.width() - self.corner_size and pos.y() > self.height() - self.corner_size
    
    def drawCorner(self, painter):
        """ Draws a corner grabber in the bottom right corner of the widget.

        Args:
            painter (QPainter): The painter object to draw with.
        """
        rect = QRect(self.width() - self.corner_size, self.height() - self.corner_size, self.corner_size, self.corner_size)
        painter.setBrush(QColor(100, 100, 100))
        painter.drawRect(rect)
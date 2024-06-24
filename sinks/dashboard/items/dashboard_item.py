from pyqtgraph.Qt.QtGui import QPainter, QColor
from pyqtgraph.Qt.QtWidgets import QWidget, QHeaderView
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import ActionParameter, ActionParameterItem
from pyqtgraph.Qt.QtCore import QRect, Qt

from collections import OrderedDict
import json

from .no_text_action_parameter import NoTextActionParameter


class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    To create a new dashboard item, subclass this class and implement the following methods:
        - get_name() ;  just the name, has to be static
        - add_parameters() ; return a list of pyqtgraph Parameter objects specific to the widget
    """

    """Whether the dashboard item is locked, which disables selection"""

    def __init__(self, resize_callback, params=None):
        super().__init__()
        self.setMouseTracking(True)
        self.corner_grabbed = False
        self.corner_in = False
        self.corner_size = 40
        self.corner_index = 0
        self.resize_callback = resize_callback
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
    
    # The following functions are used to make the widget resizable by dragging the bottom right corner.

    def mousePressEvent(self, event):
        """ Starts resizing the widget when the mouse is pressed in the bottom right corner.
        Notes:
            if the mouse is not in the bottom right corner, the event is passed to the base class method for normal processing.
        """
        if self.is_in_corner(event.pos()):
            self.corner_grabbed = True
            self.grab_start_pos = event.globalPos()
            self.start_rect = self.rect()
        else:
            super().mousePressEvent(event)  # Call the base class method for normal processing

    def mouseMoveEvent(self, event):
        """ 
        Resizes the widget while the mouse is being moved.
        """
        # self.corner_in = self.is_in_corner(event.pos())
        
        if self.is_in_corner(event.pos()):
            self.setCursor(Qt.SizeFDiagCursor)
            self.corner_in = True
            self.corner_index = self.index_corner(event.pos())
        else:
            self.setCursor(Qt.ArrowCursor)
            self.corner_in = False

        if self.corner_grabbed:
            delta = event.globalPos() - self.grab_start_pos
            new_width = max(self.start_rect.width() + delta.x(), self.minimumWidth())
            new_height = max(self.start_rect.height() + delta.y(), self.minimumHeight())
            self.resize(new_width, new_height)

    def mouseReleaseEvent(self, event):
        """ Stops resizing the widget when the mouse is released.
        Args:
            event (QMouseEvent): The mouse release event.
        """
        self.corner_grabbed = False

    def is_in_corner(self, pos):
        left_up_corner = pos.x() < self.corner_size and pos.y() < self.corner_size
        right_up_corner = pos.x() > self.width() - self.corner_size and pos.y() < self.corner_size
        left_down_corner = pos.x() < self.corner_size and pos.y() > self.height() - self.corner_size
        right_down_corner = pos.x() > self.width() - self.corner_size and pos.y() > self.height() - self.corner_size
        # return right_down_corner
        return left_down_corner or right_down_corner or left_up_corner or right_up_corner
    
    
    # Consider Ignore drawing instead chage Cursor shape (Degress Latency)
    
    def index_corner(self, pos):
        left_up_corner = pos.x() < self.corner_size and pos.y() < self.corner_size
        right_up_corner = pos.x() > self.width() - self.corner_size and pos.y() < self.corner_size
        left_down_corner = pos.x() < self.corner_size and pos.y() > self.height() - self.corner_size
        right_down_corner = pos.x() > self.width() - self.corner_size and pos.y() > self.height() - self.corner_size
        return [left_up_corner, right_up_corner, left_down_corner, right_down_corner].index(True)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        self.draw_corner(painter)


    def draw_corner(self, painter):
        """ Draws a corner grabber in the bottom right corner of the widget.
        Args:
            painter (QPainter): The painter object to draw with.
        """

        left_up_rect = QRect(0, 0, self.corner_size, self.corner_size)
        right_up_rect = QRect(self.width() - self.corner_size, 0, self.corner_size, self.corner_size)
        left_down_rect = QRect(0, self.height() - self.corner_size, self.corner_size, self.corner_size)
        right_down_rect = QRect(self.width() - self.corner_size, self.height() - self.corner_size, self.corner_size, self.corner_size)
        rect_lst = [left_up_rect, right_up_rect, left_down_rect, right_down_rect]
        painter.setPen(Qt.NoPen)  # Hide the outline of the rectangle
        painter.setBrush(Qt.NoBrush)  # Hide the fill color of the rectangle

        painter.drawRect(left_up_rect)
        painter.drawRect(right_up_rect)
        painter.drawRect(left_down_rect)
        painter.drawRect(right_down_rect)

        if self.corner_in:
            painter.setBrush(QColor(100, 100, 100))
            painter.drawRect(rect_lst[self.corner_index]) 


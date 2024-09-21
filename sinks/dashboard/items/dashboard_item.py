from pyqtgraph.Qt.QtGui import QPainter, QColor
from pyqtgraph.Qt.QtWidgets import QWidget, QHeaderView
from pyqtgraph.parametertree import Parameter, ParameterTree
from pyqtgraph.parametertree.parameterTypes import ActionParameter, ActionParameterItem
from pyqtgraph.Qt.QtCore import QRect, Qt

from collections import OrderedDict
import json

from .no_text_action_parameter import NoTextActionParameter
from .series_parameter import SeriesChecklistParameter, SeriesListParameter


class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    To create a new dashboard item, subclass this class and implement the following methods:
        - get_name() ;  just the name, has to be static
        - add_parameters() ; return a list of pyqtgraph Parameter objects specific to the widget
    """

    def __init__(self, dashboard, params=None):
        super().__init__()
        self.dashboard = dashboard
        self.setMouseTracking(True)
        self.corner_grabbed = False
        self.corner_in = False
        self.corner_size = self.dynamic_corner_size()
        self.corner_index = 3 # 0: left up, 1: right up, 2: left down, 3: right down
        self.temp_pos = None # Used to store the temp position of the widget when resizing
        self.resize_callback = dashboard.on_item_resize
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
        parameters = self.add_parameters()
        self.parameters.addChildren(parameters)

        refreshable = [p for p in parameters if isinstance(p, SeriesListParameter) or isinstance(p, SeriesChecklistParameter)]

        class CustomParameterTree(ParameterTree):
            def __init__(self):
                super().__init__(showHeader=True)

            def show(self):
                super().show()
                for r in refreshable:
                    r.refresh_limits()            

        self.parameter_tree = CustomParameterTree()
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
    
    def dynamic_corner_size(self)-> int | float :
        if self.dashboard.mouse_resize:
            return min(100, max(min(self.width(), self.height())/10,1))
        else:
            return 0

    def mousePressEvent(self, event):
        """ Starts resizing the widget when the mouse is pressed in the bottom right corner.
        Notes:
            if the mouse is not in the corner, the event is passed to the base class method for normal processing.
        """
        if self.dashboard.mouse_resize and not self.dashboard.locked and self.corner_hit(event.pos()):
            # Check item itself isn't locked
            for rect, pair in self.dashboard.widgets.items():
                if pair[1] == self and rect in [widget[0] for widget in self.dashboard.locked_widgets]:
                    super().mousePressEvent(event)
                    return

            self.corner_grabbed = True
            self.grab_start_pos = self.dashboard.view.mapToScene(event.globalPos())
            self.start_rect = self.rect()
        else:
            super().mousePressEvent(event)  # Call the base class method for normal processing

    def mouseMoveEvent(self, event): # This function is called when the mouse is move in the widget
        """
        When the mouse is move in the corner, the cursor shape is changed to indicate that the widget can be resized
        """
        if self.dashboard.mouse_resize and not self.dashboard.locked and self.corner_hit(event.pos()):
            self.setCursor(Qt.SizeAllCursor)
            self.corner_in = True
        else:
            self.setCursor(Qt.ArrowCursor)
            self.corner_in = False

        if self.corner_grabbed:
            if self.temp_pos is None:
                self.temp_pos = self.pos()
            delta = self.dashboard.view.mapToScene(event.globalPos()) - self.grab_start_pos
            
            new_width =  max(self.start_rect.width() + delta.x(), self.minimumWidth()) if self.corner_index == 1 or self.corner_index == 3 else max(self.start_rect.width() - delta.x(), self.minimumWidth())
            new_height = max(self.start_rect.height() + delta.y(), self.minimumHeight()) if self.corner_index == 2 or self.corner_index == 3 else max(self.start_rect.height() - delta.y(), self.minimumHeight())
            
            if self.corner_index == 0:
                self.setGeometry(self.temp_pos.x() + delta.x(), self.temp_pos.y() + delta.y(), new_width, new_height)
            elif self.corner_index == 1:
                self.setGeometry(self.pos().x(), self.temp_pos.y() + delta.y(), new_width, new_height)
            elif self.corner_index == 2:
                self.setGeometry(self.temp_pos.x() + delta.x(), self.pos().y(), new_width, new_height)
            elif self.corner_index == 3:
                self.setGeometry(self.pos().x(), self.pos().y(), new_width, new_height)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """
        Stops resizing the widget when the mouse is released.
        """
        # Reset all the states
        if self.dashboard.mouse_resize and not self.dashboard.locked:
            self.corner_grabbed = False
            self.corner_in = False
            self.temp_pos = None
            # corner_size is updated to be proportional to the widget size
            self.corner_size = self.dynamic_corner_size()
        else:
            super().mouseReleaseEvent(event)

    def corner_hit(self, pos):
        """
        Checks if the mouse is in the corner and updates the corner_index.
        """
        right_down_corner = pos.x() >= self.width() - self.corner_size and pos.y() >= self.height() - self.corner_size
        # For Small widgets, the corner grabber is only in the bottom right corner
        if self.corner_size < 15:
            self.corner_index = 3
            return right_down_corner
        left_up_corner = pos.x() <= self.corner_size and pos.y() <= self.corner_size
        right_up_corner = pos.x() >= self.width() - self.corner_size and pos.y() <= self.corner_size
        left_down_corner = pos.x() <= self.corner_size and pos.y() >= self.height() - self.corner_size
        index_list = [left_up_corner, right_up_corner, left_down_corner, right_down_corner]
        if any(index_list):
            self.corner_index = index_list.index(True)
            return True
        else:
            return False

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.corner_in: # Draw the corner grabber when the mouse is in the corner
            self.draw_corner(painter)


    def draw_corner(self, painter):
        """
        Draws a corner grabber in the bottom right corner of the widget.
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


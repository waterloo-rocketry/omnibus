from pyqtgraph.Qt.QtWidgets import QWidget
from pyqtgraph.parametertree import Parameter
from collections import OrderedDict
import json


class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    To create a new dashboard item, subclass this class and implement the following methods:
        - get_name() ;  just the name, has to be static
        - add_parameters() ; return a list of pyqtgraph Parameter objects specific to the widget
    """

    def __init__(self, params=None):
        super().__init__()
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

        # add listeners before restoring state so that the
        # dimensions are set correctly from the saved state
        self.parameters.child("width").sigValueChanging.connect(self.handle_dimensions_changed)
        self.parameters.child("height").sigValueChanging.connect(self.handle_dimensions_changed)

        # restore state is params are provided
        if params:
            state = json.loads(params, object_pairs_hook=OrderedDict)
            self.parameters.restoreState(state, addChildren=True, blockSignals=True, recursive=True)

        self.setStyleSheet("background-color: white; border: 5px solid blue;")

    def resizeEvent(self, event):
        print("resizeEvent", event)
        with self.parameters.treeChangeBlocker():
            self.parameters.child("width").setValue(self.size().width())
            self.parameters.child("height").setValue(self.size().height())

    def handle_dimensions_changed(self, param, value):
        """
        This is to resize widget when the dimension value in parameter_tree is changed
        """
        height = width = 0
        if param.name() == "width":
            width = value
            height = self.parameters.child("height").value()
        elif param.name() == "height":
            height = value
            width = self.parameters.child("width").value()
        print("handle_dimensions_changed", width, height)
        self.resize(width, height)
        print("resized to", self.size())

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

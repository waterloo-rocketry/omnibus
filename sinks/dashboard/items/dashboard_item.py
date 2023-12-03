from pyqtgraph.Qt.QtWidgets import QWidget, QHeaderView
from pyqtgraph.parametertree import Parameter, ParameterTree
from collections import OrderedDict
import json

from .parsley_instance import PARSLEY_INSTANCE

class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    To create a new dashboard item, subclass this class and implement the following methods:
        - get_name() ;  just the name, has to be static
        - add_parameters() ; return a list of pyqtgraph Parameter objects specific to the widget
    """

    def __init__(self, resize_callback, params=None):
        super().__init__()

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

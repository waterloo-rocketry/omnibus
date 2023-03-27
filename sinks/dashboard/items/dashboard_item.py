from pyqtgraph.Qt.QtWidgets import QWidget
from pyqtgraph.parametertree import Parameter


class DashboardItem(QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    """

    def __init__(self):
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
            { "name": "Width", "type": "int", "default": 100 },
            { "name": "Height", "type": "int", "default": 100 }
        ])

        self.parameters.child("Width").sigValueChanged.connect(lambda _, val:
            self.resize(val, self.size().height())
        )
        self.parameters.child("Height").sigValueChanged.connect(lambda _, val:
            self.resize(self.size().width(), val)
        )

    def resizeEvent(self, _):
        with self.parameters.treeChangeBlocker():
            self.parameters.child("Width").setValue(self.size().width())
            self.parameters.child("Height").setValue(self.size().height())

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

    def on_delete(self):
        """
        This function is called when a dashitem is removed from the screen. In practice, this will likely be used to
        remove subscriptions from series
        """
        pass

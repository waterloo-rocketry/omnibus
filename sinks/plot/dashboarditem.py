import typing
from pyqtgraph.Qt import QtWidgets

class DashboardItem:
    """
    Abstract superclass of all dashboard items to define the common interface.
    """
    def __init__(self, props=None):
        """
        Create the dashboard item (get ready for child() to be called), optionally initializing with the properties
        we saved from a previous run.
        """
        raise NotImplementedError

    def save(self) -> typing.Any:
        """
        Return whatever data we need to recreate ourselves. This data gets passed to the constructor when reinitializing.
        """
        raise NotImplementedError

    def child(self) -> QtWidgets:
        """
        Return Qt Widget that encompasses this DashboardItem
        """
        raise NotImplementedError

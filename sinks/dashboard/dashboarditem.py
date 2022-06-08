import typing
from pyqtgraph.Qt import QtWidgets
import sip


class DashboardItem:
    """
    Abstract superclass of all dashboard items to define the common interface.
    """

    def __init__(self, props=None):
        """
        Create the dashboard item (get ready for child() to be called), optionally initializing with the properties
        we saved from a previous run.
        """
        self.subscribed_series = []

    def get_props(self) -> typing.Any:
        """
        Return whatever data we need to recreate ourselves. This data gets passed to the constructor when reinitializing.
        """
        raise NotImplementedError

    def get_widget(self) -> QtWidgets.QWidget:
        """
        Return Qt Widget that encompasses this DashboardItem
        """
        raise NotImplementedError

    def subscribe_to_series(self, series):
        """
        Ensures that whenever a series' data is updated,
        the on_data_update method is called
        """
        series.add_observer(self)
        self.subscribed_series.append(series)

    def unsubscribe_to_all(self):
        for series in self.subscribed_series:
            series.remove_observer(self)

    def on_data_update(self, series):
        """
        Whenever data is updated in a series that we are subscribed
        to, this method is called. The series that was updated is supplied
        as a parameter
        """
        pass

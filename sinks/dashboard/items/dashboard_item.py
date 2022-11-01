import typing
from pyqtgraph.Qt import QtWidgets
from utils import prompt_user


class DashboardItem(QtWidgets.QWidget):
    """
    Abstract superclass of all dashboard items to define the common interface.
    """

    def __init__(self, props=None):
        """
        Create the dashboard item (get ready for child() to be called), optionally initializing with the properties
        we saved from a previous run.
        """
        super().__init__()
        self.subscribed_series = []

    def get_name():
        '''
        Return a nicer name for the Dash Item instead of the class name
        '''
        #raise NotImplementedError
        return "Kavin was here"

    def get_props(self) -> typing.Any:
        """
        Return whatever data we need to recreate ourselves. This data gets passed to the constructor when reinitializing.
        """
        raise NotImplementedError

    def on_data_update(self, series):
        """
        Whenever data is updated in a series that we are subscribed
        to, this method is called. The series that was updated is supplied
        as a parameter
        """
        pass

    def subscribe_to_series(self, series):
        """
        Ensures that whenever a series' data is updated,
        the on_data_update method is called
        """
        series.add_observer(self)
        self.subscribed_series.append(series)

    def unsubscribe_to_all(self):
        """
        A helper function, designed to unsubscribe 
        this dash item from all series its subscribed 
        to
        """
        for series in self.subscribed_series:
            series.remove_observer(self)

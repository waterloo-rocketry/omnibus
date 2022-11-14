import typing
from pyqtgraph.Qt import QtWidgets
from utils import prompt_user


class Subscriber():
    def __init__(self):
        self.subscribed_subjects = []

    def subscribe_to(self, subject):
        """
        Ensures that whenever a series' data is updated,
        the on_data_update method is called
        """
        subject.add_observer(self)
        self.subscribed_subjects.append(subject)

    def unsubscribe_to_all(self):
        """
        A helper function, designed to unsubscribe 
        this dash item from all series its subscribed 
        to
        """
        for subject in self.subscribed_subjects:
            subject.remove_observer(self)

    def on_data_update(self, series):
        """
        Whenever data is updated in a series that we are subscribed
        to, this method is called. The series that was updated is supplied
        as a parameter
        """
        pass


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

    def get_name():
        '''
        Return a nicer name for the Dash Item instead of the class name
        '''
        raise NotImplementedError

    def get_props(self) -> typing.Any:
        """
        Return whatever data we need to recreate ourselves. This data gets passed to the constructor when reinitializing.
        """
        raise NotImplementedError

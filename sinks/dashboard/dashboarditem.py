import typing
from pyqtgraph.Qt import QtWidgets
import sip


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



    def get_props(self) -> typing.Any:
        """
        Return whatever data we need to recreate ourselves. This data gets passed to the constructor when reinitializing.
        """
        raise NotImplementedError

    # def get_widget(self) -> QtWidgets.QWidget:
    #     """
    #     Return Qt Widget that encompasses this DashboardItem
    #     """
    #     raise NotImplementedError

    def prompt_user(self, property_name, description, prompt_type, items=None):
        ok = False
        selection = None
        
        if prompt_type == "items":
            if (items == None):
                raise RuntimeError

            selection, ok = QtWidgets.QInputDialog.getItem(self, property_name, description, items, 0, False)    
            
        elif prompt_type == "text":
            selection, ok = QInputDialog.getText(self, property_name, description)

        elif prompt_type == "number":
            selection, ok = QInputDialog.getDouble(self, property_name, description)

        if not ok:
            raise RuntimeError

        return selection

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
        for series in self.subscribed_series:
            series.remove_observer(self)

import typing
import ..parsers import Parser
import Plot from Dashboard
from pyqtgraph.Qt.Wtwidgets import QWidget


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

    def child(self) -> QWidget:
        """
        Return Qt Widget that encompasses this DashboardItem
        """
        raise NotImplementedError

class PlotDashItem (DashboardItem):
    def __init__(self, props = None):
        self.serie = None
        if props is not None:
            self.serie = Parser.get_serie(props[0], props[1]) 
            self.plot = Plot(self.serie)
        else:
            pass # add a prompt here to do a get_serie_all and fill the get_serie! It's left as WIP for add button

        self.widget = pg.PlotWidget(plotItem = self.plot)
    
    def save(self):
        return [self.serie.channel, self.serie.name]

    def child(self):
        return self.widget

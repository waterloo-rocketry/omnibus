import typing
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
    def __init__(self, props):
        self.serie = get_serie(props["serie_name"]) 
        if self.serie is not None:
            self.plot = Plot(self.serie)
        self.widget = pg.PlotWidget(plotItem = self.plot)
    def save(self):
        return {"serie_name": self.serie.name}

    def child(self):
        return self.widget


class Dashboard:
    def load(file):
        data = pickle.deserialize(file)
        for k, v in data["items"].items(): # { 0: {...}, 1: ..., ...}
            if v["class"] == "plot":
                item = Plot(v["props"])
                dock = Dock(name=k)
                dock.addWidget(item.child())
                dockarea.addDock(dock)
        dockarea.restoreState(data["layout"]) # pyqtgraph dock layout

    def save(file):
        data = {}
        data["layout"] = dockarea.saveState()
        for k, item in self.items.items():
            data["items"][k] = {"props": item.save(), "class": type(item)}


    def get_serie(name):
        for parser in Parser.parsers:
            if parser.series.values().name == name:
                return parser.series.values()
        return None

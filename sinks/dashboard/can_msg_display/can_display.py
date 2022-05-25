import signal

import pyqtgraph as pg
from pyqtgraph.dockarea.Dock import Dock
from pyqtgraph.dockarea.DockArea import DockArea
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from sinks.plot.parsers import Parser


class CanMessageDisplay:
    """
    Display for CAN messages.
    """

    def __init__(self, callback):
        self.callback = callback

        self.series = Parser.get_series()
        self.series.register_update(self.update)

        # temporarily running dock/app through this class for testing, but this will be a dashitem eventually
        self.app = pg.mkQApp("App")
        self.win = QtWidgets.QMainWindow()
        self.win.setWindowTitle('CAN Message Display')
        self.win.resize(1000, 600)
        self.area = DockArea()
        self.win.setCentralWidget(self.area)

        self.text_browser = QtWidgets.QTextBrowser()
        dock = Dock(name=str(0))
        dock.addWidget(self.text_browser)
        self.area.addDock(dock, 'right')
        self.exec()

    def update(self):
        print(str(self.callback))
        # temp fix for not constantly pushing update label string to the browser
        if str(self.callback)[0:9] != "<function":
            self.text_browser.append(str(self.callback))
        self.callback()

    # Not currently used
    def exec(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(16)

        # make ctrl+c close the window
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self.win.show()
        pg.mkQApp().exec_()

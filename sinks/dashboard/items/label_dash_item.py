from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout, QMenu
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter
from pyqtgraph.Qt.QtCore import QEvent
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget


from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

from pyqtgraph.Qt.QtWidgets import QLabel

import numpy as np

from .dashboard_item import DashboardItem
import config
from utils import prompt_user
from .registry import Register


@Register
class LabelDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        series_param = ChecklistParameter(name='Series',
                                          type='list',
                                          value=[],
                                          itemClass=ChecklistParameter,
                                          limits=publisher.get_all_streams())

        self.parameters.addChild(series_param)

        # a list of series names to be displayed
        self.series = self.parameters.param('Series').value()
        self.parameters.param('Series').sigValueChanged.connect(self.on_series_change)

        # dict of the type of messages that should be displayed
        # with series names as the key
        # and the msg_type to be displayed as the value
        # self.display_msg_type = props["display"]

        # debug print,
        # but might be useful to leave in
        # print(self.display_msg_type)

        # save props as a field
        # self.props = props

        # storing the data to be displayed of a series,
        # with series names as keys and the data as value
        self.data = {}
        # initalise to 0
        for s in self.series:
            self.data[s] = 0

        # The title the label is displaying
        self.title = "Select series to continue"

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # create the label widget
        self.widget = QLabel(self)
        # wrap text
        self.widget.setWordWrap(True)
        # just some default text that will be over-written on update
        self.widget.setText(self.title)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def on_series_change(self, param, value):
        if len(value) > 6:
            self.parameters.param('Series').setValue(value[:6])
        self.series = self.parameters.param('Series').childrenValue()
        print(self.series)
        # resubscribe to the new streams
        publisher.unsubscribe_from_all(self.on_data_update)
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

    def on_data_update(self, stream, payload):
        time, data = payload

        self.title = f"{stream}: {data}"

        # i cant believe, and i dont want to believe, that the syntax
        # for styling qlabel text is,,
        #   <font color=\"blue\">hello, world</font>
        # Note: <br> is same as \n, but \n won't work with above syntax
        # for s in self.series:
            # the data is initalised to 0, this is to prevent us from accessing it
            # if type(self.data[s]) is not int:
            #     self.title += f"{s} <font color=\"gray\">-- Message Type: {self.data[s]['msg_type']} -- </font><br>"

            #     for data_keys in self.data[s]['data']:
            #         self.title += f"<font color=\"#e0d000\">{data_keys}:</font> {self.data[s]['data'][data_keys]}<br>"
            #     self.title += "<br>"

        self.widget.setText(self.title)

    @staticmethod
    def get_name():
        return "Label"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

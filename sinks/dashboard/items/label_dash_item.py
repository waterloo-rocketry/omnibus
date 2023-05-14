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
from pyqtgraph.parametertree import Parameter

import numpy as np

from .dashboard_item import DashboardItem
import config
from .registry import Register

# props
#   board ID - only consider messages with that ID, Text input
#   msg ID -
#   Field you want to be displayed

# How to format??
# Change the background colour based on values incoming

# Arbitray length list rule structure,
# each rule is a colour and a condition
# different condition for strings and for numbers

@Register
class LabelDashItem(DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item onstructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        series_param = ChecklistParameter(name='Series',
                                          type='list',
                                          value=[],
                                          itemClass=ChecklistParameter,
                                          limits=publisher.get_all_streams())

        # What msg should be displayed?
        msgType_param = {'name':'MsgType', 'type': 'str', 'value': ''}
        boardId_param = {'name':'BoardID', 'type': 'str', 'value': ''}

        self.parameters.addChildren([series_param, msgType_param, boardId_param])

        if params:
            self.parameters.param('Series').setValue(params['Series'])
            self.parameters.param('MsgType').setValue(params['MsgType'])
            self.parameters.param('BoardID').setValue(params['BoardID'])
            self.parameters.param('Width').setValue(params['Width'])
            self.parameters.param('Height').setValue(params['Height'])

        # on change
        self.parameters.param('Series').sigValueChanged.connect(self.on_series_change)
        # a list of series names to be displayed
        self.series = self.parameters.param('Series').value()

        # What msg should be display?
        self.parameters.param('MsgType').sigValueChanged.connect(self.on_msg_type_change)
        self.msg_type = self.parameters.param('MsgType').value()

        self.parameters.param('BoardID').sigValueChanged.connect(self.on_board_id_change)
        self.board_id = self.parameters.param('BoardID').value()

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
        if len(value) == 0:
            self.widget.setText("")
        if len(value) > 6:
            self.parameters.param('Series').setValue(value[:6])
        self.series = self.parameters.param('Series').childrenValue()
        print(self.series)
        # resubscribe to the new streams
        publisher.unsubscribe_from_all(self.on_data_update)
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)
        self.data = {}

    def on_msg_type_change(self, param, value):
        self.msg_type = self.parameters.param('MsgType').value()
        self.data = {}

    def on_board_id_change(self, param, value):
        self.board_id = self.parameters.param('BoardID').value()
        self.data = {}

    def on_data_update(self, stream, payload):
        time, data = payload

        self.title = ""

        if data['msg_type'] == self.msg_type or self.msg_type == '':
            if data['board_id'] == self.board_id or self.board_id == '':
                self.data[stream] = data

        # i cant believe, and i dont want to believe, that the syntax
        # for styling qlabel text is,,
        #   <font color=\"blue\">hello, world</font>
        # Note: <br> is same as \n, but \n won't work with above syntax
        for s in self.data:
            # the data is initalised to 0, this is to prevent us from accessing it
            self.title += f"{s}: <font color=\"#e0d000\">{self.data[s]}</font><br>"

            # for data_keys in self.data[s]:
            #     self.title += f"<font color=\"#e0d000\">{data_keys}:</font> {self.data[s]['data'][data_keys]}<br>"
            self.title += "<br>"

        self.widget.setText(self.title)

        self.widget.adjustSize()

    @staticmethod
    def get_name():
        return "Label"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout, QMenu
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
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # a list of series names to be plotted
        self.series = props["series"]

        # dict of the type of messages that should be displayed
        # with series names as the key
        # and the msg_type to be displayed as the value
        self.display_msg_type = props["display"]

        # debug print,
        # but might be useful to leave in
        print(self.display_msg_type)

        # save props as a field
        self.props = props

        # storing the data to be displayed of a series,
        # with series names as keys and the data as value
        self.data = {}
        # initalise to 0
        for s in self.series:
            self.data[s] = 0

        # The title the label is displaying
        self.title = ""

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # create the label widget
        self.widget = QLabel(self)
        # wrap text
        self.widget.setWordWrap(True)
        # just some default text that will be over-written on update
        self.widget.setText(("\n").join(self.series))

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    # overriding QWidget method to create custom context menu
    # needs to be re-done for a label
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        change_threshold = menu.addAction('Change threshold')

        action = menu.exec_(event.globalPos())
        if action == change_threshold:
            threshold_input = prompt_user(
                self,
                "Threshold Value",
                "Set an upper limit",
                "number",
                cancelText="No Threshold"
            )
            self.limit = threshold_input
            self.props["limit"] = threshold_input
            # if user changes threshold to No threshold
            if self.limit is None:
                self.warning_line.setData([], [])
                self.warning_line.setFillLevel(None)

    def prompt_for_properties(self):

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "Select the series you wish to display. Up to 6 if displaying together.",
            "checkbox",
            publisher.get_all_streams(),
        )
        if not channel_and_series[0]:
            return None
        # if more than 6 series are selected, only display the first 6
        if len(channel_and_series) > 6:
            channel_and_series = channel_and_series[:6]

        if channel_and_series[1]:     # display separately
            props = [{"series": [series], "display": {}} for series in channel_and_series[0]]
        else:                           # display together
            # if more than 6 series are selected, only display the first 6
            if len(channel_and_series) > 6:
                channel_and_series = channel_and_series[:6]
            props = [{"series": channel_and_series[0], "display": {}}]

        # ask the user about what type of messages they want to see displayed
        for s in props:
            # for series displayed together
            if type(s["series"]) is list:
                for s2 in s["series"]:
                    msg_type = prompt_user(
                        self,
                        "Message Type",
                        f"What message type would you like to display for {s2}. Leave blank for all message types.",
                        "text",
                    )
                    s["display"][s2] = msg_type
            else:
            # for series displayed separately
                msg_type = prompt_user(
                        self,
                        "Message Type",
                        f"What message type would you like to display for {s['series']}. Leave blank for all message types.",
                        "text",
                )
                s["display"][s["series"]] = msg_type  # awkward syntax, but it leads to
        return props                                  # {... "display": {series_name: msg_type}}

    def on_data_update(self, stream, payload):
        # time, point = payload

        # self.widget.setText(str(point))
        time, data = payload

        # if display msg type is blank then the user input nothing and wants all messages
        if (data["msg_type"] == self.display_msg_type[stream]) or (self.display_msg_type[stream] == ''):
            self.data[stream] = data

        self.title = ""

        # i cant believe, and i dont want to believe, that the syntax
        # for styling qlabel text is,,
        #   <font color=\"blue\">hello, world</font>
        # Note: <br> is same as \n, but \n won't work with above syntax
        for s in self.series:
            # the data is initalised to 0, this is to prevent us from accessing it
            if type(self.data[s]) is not int:
                self.title += f"{s} <font color=\"gray\">-- Message Type: {self.data[s]['msg_type']} -- </font><br>"

                for data_keys in self.data[s]['data']:
                    self.title += f"<font color=\"#e0d000\">{data_keys}:</font> {self.data[s]['data'][data_keys]}<br>"
                self.title += "<br>"

        self.widget.setText(self.title)

    def get_props(self):
        return self.props

    @staticmethod
    def get_name():
        return "Label"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

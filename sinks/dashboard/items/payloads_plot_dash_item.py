from publisher import publisher
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph as pg
from pyqtgraph.console import ConsoleWidget
import pyqtgraph.opengl as gl
from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

import numpy as np

from sinks.dashboard.items.dashboard_item import DashboardItem
import config
from utils import prompt_user
import time

#if there is error for opengl use the following command to install the acc : sudo easy_install pyopengl
from .registry import Register


@Register
class PayloadDashItem (DashboardItem):
    def __init__(self, props):
        # Call this in **every** dash item constructor
        super().__init__()

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        # save props as a field
        self.props = props

        # initilize 3D environment
        self.view = gl.GLViewWidget()
        self.view.setCameraPosition(distance=40)
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 0)
        self.view.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 0)
        self.view.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, -10)
        self.view.addItem(gz)

        # subscribe to stream dictated by properties
        if self.props[1]:
            publisher.subscribe(self.props[0], self.on_data_update_orientation)
            self.xaxis = gl.GLLinePlotItem()
            self.view.addItem(self.xaxis)
            self.yaxis = gl.GLLinePlotItem()
            self.view.addItem(self.yaxis)
            self.zaxis = gl.GLLinePlotItem()
            self.view.addItem(self.zaxis)
            self.orientation = (0, 0, 0) # Euler Angles
        else:
            publisher.subscribe(self.props[0], self.on_data_update_position)
            self.pos_list = []
            self.line = gl.GLLinePlotItem()
            self.view.addItem(self.line)

        # add it to the layout
        self.layout.addWidget(self.view, 0, 0)
        self.start_time = time.time()

        # create the plot
        self.plot = pg.PlotItem(title=self.props[0], left="Data", bottom="Seconds")
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.hideButtons()

        self.curve = self.plot.plot(self.times, self.points, pen='y')
        if self.limit is not None:
            self.warning_line = self.plot.plot([], [], brush=(255, 0, 0, 50), pen='r')


        pos = np.random.random(size=(100000,3))
        pos *= [10,-10,10]
        pos[0] = (0,0,0)
        color = np.ones((pos.shape[0], 4))
        size = np.random.random(size=pos.shape[0])*10
        self.widget = gl.GLScatterPlotItem(pos=pos, color=(1,1,1,1), size=size)
        # create the plot widget
       
    
        w = gl.GLViewWidget()
        w.show()
        w.setCameraPosition(distance=40)
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 0)
        w.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 0)
        w.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, -10)
        w.addItem(gz)
        w.addItem(self.widget)
        

        # add it to the layout
        self.layout.addWidget(w, 0, 0)

    def prompt_for_properties(self):

        orientation_mode = prompt_user(
            self,
            "Orientation Mode",
            "Is the data a position or orientation?",
            "items",
            ["Position", "Orientation"]
        )

        enable_orientation = True if orientation_mode == "Orientation" else False

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None

        return [channel_and_series, enable_orientation]

    def on_data_update_position(self, payload):
        time, point = payload
        self.pos_list.append(tuple(point))
        if len(self.pos_list) > 200:
            self.pos_list.pop(0)

        self.line.setData(pos=self.pos_list, color=(1.0,1.0,1.0,1.0))

    def on_data_update_orientation(self, payload):
        time, orientation = payload

        xlist = [(0,0,0), self.transform((10, 0, 0), orientation)]
        ylist = [(0,0,0), self.transform((0, 10, 0), orientation)]
        zlist = [(0,0,0), self.transform((0, 0, 10), orientation)]

        self.xaxis.setData(pos=xlist, color=(1.0,0.0,0.0,1.0))
        self.yaxis.setData(pos=ylist, color=(0.0,1.0,0.0,1.0))
        self.zaxis.setData(pos=zlist, color=(0.0,0.0,1.0,1.0))

    def transform(self, point, euler_angle):
        return self.Rx(self.Ry(self.Rz(point, euler_angle[0]), euler_angle[1]), euler_angle[2])

    def Rz(self, point, gamma):
        x, y, z = point

        return (
            np.cos(gamma)*x - np.sin(gamma)*y,
            np.sin(gamma)*x + np.cos(gamma)*y,
            z
            )

    def Ry(self, point, beta):
        x, y, z = point

        return (
            np.cos(beta)*x + np.sin(beta)*z,
            y,
            -np.sin(beta)*x + np.cos(beta)*z
            )

    def Rx(self, point, alpha):
        x, y, z = point

        return (
            x,
            np.cos(alpha)*y - np.sin(alpha)*z,
            np.sin(alpha)*y + np.cos(alpha)*z
            )
        # threshold_input == None if not set
        threshold_input = prompt_user(
            self,
            "Threshold Value",
            "Set an upper limit",
            "number",
            cancelText="No Threshold"
        )

        props = [channel_and_series, threshold_input]

        return props

    def on_data_update(self, payload):
        time, point = payload
        desc = payload[2] if (len(payload) > 2) else ""

        time += self.time_offset

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last == 0:  # is this the first point we're plotting?
            self.times.fill(time)  # prevent a rogue datapoint at (0, 0)
            self.points.fill(point)
            self.sum = self.avgSize * point

        self.last += 1 / config.GRAPH_RESOLUTION

        self.sum -= self.points[self.size - self.avgSize]
        self.sum += point

        # add the new datapoint to the end of each array, shuffle everything else back
        self.times[:-1] = self.times[1:]
        self.times[-1] = time
        self.points[:-1] = self.points[1:]
        self.points[-1] = point

        min_point = min(self.points)
        max_point = max(self.points)

        # set the displayed range of Y axis
        #self.plot.setYRange(min_point, max_point, padding=0.1)

        if self.limit is not None:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData([self.times[0], self.times[-1]], [self.limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)

        # plot the data curve
        #self.curve.setData(self.times, self.points)
        # current value readout in the title
        #self.plot.setTitle(
            #f"[{sum(self.points)/len(self.points): <4.4f}] [{self.points[-1]: <4.4f}] {self.props[0]}")
        
 

    def get_props(self):
        return self.props

    def get_name():
        return "Payload Plot"

    def on_delete(self):
        if self.props[1]:
            publisher.unsubscribe_from_all(self.on_data_update_orientation)
        else:
            publisher.unsubscribe_from_all(self.on_data_update_position)

if __name__ == '__main__':    
    pg.exec()
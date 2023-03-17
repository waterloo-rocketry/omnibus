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

pos_list = []

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

        self.w = gl.GLViewWidget()

        pos = np.random.random(size=(1,3))
        pos *= [10,-10,10]
        pos[0] = (0,0,0)
        size = np.random.random(size=pos.shape[0])*10
        self.widget = gl.GLLinePlotItem() #pos=pos, color=(1,1,1,1), size=size

        self.w.setCameraPosition(distance=40)
        gx = gl.GLGridItem()
        gx.rotate(90, 0, 1, 0)
        gx.translate(-10, 0, 0)
        self.w.addItem(gx)
        gy = gl.GLGridItem()
        gy.rotate(90, 1, 0, 0)
        gy.translate(0, -10, 0)
        self.w.addItem(gy)
        gz = gl.GLGridItem()
        gz.translate(0, 0, -10)
        self.w.addItem(gz)
        self.w.addItem(self.widget)

        # add it to the layout
        self.layout.addWidget(self.w, 0, 0)

       

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
        
        pos = (payload[1]*10,payload[1]*10,payload[1]*10)
        pos_list.append(pos)
        #pos *= [10,-10,10]
        pos_array = np.array(pos_list)

        size = [[1]]
        color = np.empty((53, 4))
        z = 0.5
        d = 6.0
        print(pos_list)
        self.widget.setData(pos=pos_array, color=(1.0,1.0,1.0,1.0))
        #drawing_variable = gl.GLLinePlotItem(pos = pos_list, width = 1, antialias = True)   #make a variable to store drawing data(specify the points, set antialiasing)
        #self.w.addItem(drawing_variable) #draw the item

        #drawing_variable = gl.GLLinePlotItem(pos = pos_array[0,:], color=(1.0,1.0,1.0,1.0) , antialias = True)   #make a variable to store drawing data(specify the points, set antialiasing)
       # self.w.addItem(drawing_variable) #draw the item

    

    def get_props(self):
        return self.props

    def get_name():
<<<<<<< HEAD
        return "Payload Plot"
=======
        return "Paniz Plot"
>>>>>>> 3be4bed (line plot)

    def on_delete(self):
        if self.props[1]:
            publisher.unsubscribe_from_all(self.on_data_update_orientation)
        else:
            publisher.unsubscribe_from_all(self.on_data_update_position)

if __name__ == '__main__':    
    pg.exec()
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

        # subscribe to stream dictated by properties
        publisher.subscribe(self.props[0], self.on_data_update)

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

        channel_and_series = prompt_user(
            self,
            "Data Series",
            "The series you wish to plot",
            "items",
            publisher.get_all_streams(),
        )
        if not channel_and_series:
            return None

        return [channel_and_series]

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
        return "Paniz Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

if __name__ == '__main__':    
    pg.exec()
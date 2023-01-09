import signal
import time

import numpy as np
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg
import config

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem
from pyqtgraph.graphicsItems.ImageItem import ImageItem

from PIL import Image

from parsers import Parser

class demoWindow:
    def __init__(self):
        self.win = pg.GraphicsLayoutWidget(show=True, title="Omnibus Plotter")
        self.image = Image.open("weed.png")
        self.npImg = np.asarray(self.image)
        self.npImg = np.rot90(self.npImg, axes=(1,0))
        self.imgItm = ImageItem(self.npImg)


        self.textvb = self.win.addViewBox()
        self.textvb.addItem(self.imgItm)
        self.textvb.addItem(TextItem("me_irl"))

        pg.mkQApp().exec_()


demoWindow()




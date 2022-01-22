import pyqtgraph as pg

from pyqtgraph.graphicsItems.TextItem import TextItem


class TickCounter:
    def __init__(self):
        self.win = pg.GraphicsWindow(size=(400, 400))
        self.vb = self.win.addViewBox(col=1, row=1)
        self.item = TextItem("", (255, 255, 255))
        self.vb.autoRange()
        self.item.setPos(0.25, 0.6)  # Centralize the Text
        self.vb.addItem(self.item)

    def update(self, analytics):
        text = ""
        for i in analytics:
            text += i
            text += ": "
            text += analytics[i]
            text += "\n"
        self.item.setText(text)

    def exec(self):
        pg.mkQApp().exec_()

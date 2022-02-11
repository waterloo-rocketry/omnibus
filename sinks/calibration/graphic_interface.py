import sys
from PyQt5.QtWidgets import (QApplication, QWidget,
QPushButton, QGridLayout, QLabel, QTextEdit)
from PyQt5.QtCore import QTimer
import numpy as np

import pyqtgraph as pg

from pyqtgraph.graphicsItems.LabelItem import LabelItem
from pyqtgraph.graphicsItems.TextItem import TextItem

BIG_CONSTANT = 10 ** 2
FRAME_DELAY = 500

class TextInputWidget(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.update_and_get_data = callback
        self.initUI()

    def initUI(self):
        grid = QGridLayout()  
        self.setLayout(grid)
        self.moving_average = QLabel(self)
        self.moving_average.setText('Average: ')

        self.textWidget = QTextEdit()

        self.button = QPushButton()

        self.slope = QLabel(self)
        self.slope.setText("slope: ")

        self.offset = QLabel(self)
        self.offset.setText("offset: ")

        grid.addWidget(self.moving_average)
        grid.addWidget(self.textWidget)
        grid.addWidget(self.button)
        grid.addWidget(self.slope)
        grid.addWidget(self.offset)

        self.button.clicked.connect(self.handleClick)

        row_stretches = [1,-1,3,2,2]
        for i in range(5):
            if (row_stretches[i] != -1):
                grid.setRowStretch(i,row_stretches[i])

    def getInputtedValue(self):
        return float(self.textWidget.toPlainText())

    def setMovingAverage(self, new_value):
        self.moving_average.setText(f'Average: {new_value}')

    def setSlopeAndOffset(self, new_slope, new_offset):
        self.slope.setText(f'slope: {new_slope}')
        self.offset.setText(f'offset: {new_offset}')

    def handleClick(self):
        new_data_set = self.update_and_get_data()

class CalibrationWidget(QWidget):
    def __init__(self, callback):
        super().__init__()
        #[ {'pos': [INT, INT], 'data': INT} ... ]
        self.line_plot_points = []
        # [ [INT], [INT] ]
        self.live_data_points = [
            [],
            []
        ]
        self.fetch_data = callback
        self.initUI()

    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.live_data_plot = pg.PlotWidget()
        self.live_data_line = None
        grid.addWidget(self.live_data_plot, 0, 0)

        self.line_of_best_fit = pg.PlotWidget()
        self.line_of_best_fit_line = None
        self.line_of_best_fit_scatter = pg.ScatterPlotItem(brush=pg.mkBrush(255, 255, 255, 120))
        self.line_of_best_fit.addItem(self.line_of_best_fit_scatter)
        grid.addWidget(self.line_of_best_fit, 1, 0)

        self.inputWidget = TextInputWidget(self.onButtonPress)
        grid.addWidget(self.inputWidget, 0, 1, 2, 1)

        self.timer = QTimer()
        self.timer.timeout.connect(self.renderFrame)
        self.timer.start(FRAME_DELAY)

        self.move(300, 150)
        self.setWindowTitle('Calibration Sink')
        self.show()

    def renderFrame(self):
        self.live_data_points = self.fetch_data()
        if self.live_data_line != None:
            self.live_data_line.setData(self.live_data_points[0], self.live_data_points[1])
        else:
            self.live_data_line = self.live_data_plot.plot(self.live_data_points[0], self.live_data_points[1], pen=(255,0,0))
        self.line_of_best_fit_scatter.setData(self.line_plot_points)
        if len(self.live_data_points[1]) != 0:
            self.inputWidget.setMovingAverage(sum(self.live_data_points[1]) / len(self.live_data_points[1]))

    def onButtonPress(self):
        new_y = sum(self.live_data_points[1]) / len(self.live_data_points[1])
        new_x = self.inputWidget.getInputtedValue()

        self.line_plot_points += [{'pos': [new_x, new_y], 'data':1}]

        if len(self.line_plot_points) >= 2:
            x_vals = np.array([i['pos'][0] for i in self.line_plot_points])
            y_vals = np.array([i['pos'][1] for i in self.line_plot_points])

            m, b = np.polyfit(x_vals, y_vals, 1)

            self.inputWidget.setSlopeAndOffset(m, b)

            line_x = [-BIG_CONSTANT, BIG_CONSTANT]
            line_y = [-BIG_CONSTANT * m + b, BIG_CONSTANT * m + b]

            if self.line_of_best_fit_line == None:
                self.line_of_best_fit_line = self.line_of_best_fit.plot(line_x, line_y, pen=(0,255,0))
            else:
                self.line_of_best_fit_line.setData(line_x, line_y)

            scatter_plot_x_range = (min([i['pos'][0] for i in self.line_plot_points]), max([i['pos'][0] for i in self.line_plot_points]))
            scatter_plot_y_range = (min([i['pos'][1] for i in self.line_plot_points]), max([i['pos'][1] for i in self.line_plot_points]))

            self.line_of_best_fit.setXRange(scatter_plot_x_range[0], scatter_plot_x_range[1])
            self.line_of_best_fit.setYRange(scatter_plot_y_range[0], scatter_plot_y_range[1])
        return self.line_plot_points

def initGUI(callback):
    app = QApplication(sys.argv)
    ex = CalibrationWidget(callback)
    sys.exit(app.exec_())
     
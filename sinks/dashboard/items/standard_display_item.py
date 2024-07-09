from publisher import publisher
from pyqtgraph.Qt.QtWidgets import QGridLayout, QLabel
from pyqtgraph.parametertree.parameterTypes import ListParameter
from pyqtgraph.Qt.QtGui import QFont
from pyqtgraph.Qt.QtCore import Qt
import pyqtgraph as pg

from .dashboard_item import DashboardItem
import config
from .registry import Register


@Register
class StandardDisplayItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        self.last = {}

        # storing the series name as key, its time and points as value
        # since each StandardDisplayItem can contain more than one curve
        self.times = {}
        self.points = {}

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.parameters.param('offset').sigValueChanged.connect(self.on_offset_change)
        self.parameters.param('label').sigValueChanged.connect(self.on_label_change)
        self.parameters.param('font-size').sigValueChanged.connect(self.on_font_size_change)
        self.parameters.param('display-sparkline').sigValueChanged.connect(self.on_display_sparkline_change)


        self.series = [self.parameters.param('series').value()]
        # just a single global offset for now
        self.offset = self.parameters.param('offset').value()

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # a default color list for plotting multiple curves
        # yellow green cyan white blue magenta
        self.color = ['k', 'g', 'c', 'w', 'b', 'm']

        # create the plot
        self.plot = self.create_plot()

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # Medium Text Label
        self.label = QLabel("Label")

        #Big numerical readout
        self.numRead = QLabel("Not Connected")
        
        label_font = QFont()
        label_font.setPointSize(25)
        self.label.setFont(label_font)
        num_read_font = QFont()
        num_read_font.setPointSize(25)
        self.numRead.setFont(num_read_font)

        
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.numRead, 0, 1)
        self.layout.addWidget(self.widget, 1, 0, 1, 2)
        
        self.resize(500,200)

    def add_parameters(self):
        text_param = {'name': 'label', 'type': 'str', 'value': ''}
        series_param = ListParameter(name='series',
                                    type='list',
                                    value=[],
                                    limits=publisher.get_all_streams())
        limit_param = {'name': 'limit', 'type': 'float', 'value': 0.0}
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0.0}
        font_size_param = {'name': 'font-size', 'type': 'int', 'value': 25, 'limits': (10, 30)}
        display_sparkline_param = {'name': 'display-sparkline', 'type': 'bool', 'value': True}
        return [text_param, series_param, limit_param, offset_param, display_sparkline_param, font_size_param]

    def on_series_change(self, param, value):
        self.series = [value]
        # resubscribe to the new stream
        publisher.unsubscribe_from_all(self.on_data_update)
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)
        # recreate the plot with new series and add it to the layout
        self.layout.removeWidget(self.widget)
        self.plot.close()
        self.widget.close()
        self.plot = self.create_plot()
        self.widget = pg.PlotWidget(plotItem=self.plot)
        self.layout.addWidget(self.widget, 1, 0, 1, 2)
        self.resize(self.parameters.param('width').value(),
                    self.parameters.param('height').value())

    def on_offset_change(self, _, offset):
        self.offset = offset
    
    def on_label_change(self, param, value):
        self.text = value
        self.label.setText(self.text)
    
    def on_font_size_change(self, param, value):
        # Change font size for label
        label_font = self.label.font()
        label_font.setPointSize(value)
        self.label.setFont(label_font)

        # Change font size for numerical readout
        num_read_font = self.numRead.font()
        num_read_font.setPointSize(value)
        self.numRead.setFont(num_read_font)


    def on_display_sparkline_change(self, param, value):
        if value:
            self.widget.show()
            self.layout.addWidget(self.widget, 1, 0, 1, 2)
        else:
            self.widget.hide()
            self.layout.addWidget(self.label, 0, 0)
            self.layout.addWidget(self.numRead, 0, 1)

    # Create the plot item
    def create_plot(self):
        plot = pg.PlotItem(left="Data", bottom="Seconds")
        plot.setMenuEnabled(False)     # hide the default context menu when right-clicked
        plot.setMouseEnabled(x=False, y=False)
        plot.hideButtons()
        plot.setMinimumSize(200, 50)
        if (len(self.series) > 1):
            plot.addLegend()
         # hide the axes
        plot.showAxis('left', False)
        plot.showAxis('bottom', False)
        # draw the curves
        # storing the series name as key, its plot object as value
        # update all curves every time on_data_update() is called
        self.curves = {}
        for i, series in enumerate(self.series):
            curve = plot.plot([], [], pen=self.color[i], name=series)
            self.curves[series] = curve
            self.times[series] = []
            self.points[series] = []
            self.last[series] = 0

        # initialize the threshold line, but do not plot it unless a limit is specified
        self.warning_line = plot.plot([], [], brush=(255, 0, 0, 50), pen='r')

        return plot

    def on_data_update(self, stream, payload):
        time, point = payload

        point += self.offset

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last[stream] < 1 / config.GRAPH_RESOLUTION:
            return

        self.last[stream] = time

        self.times[stream].append(time)
        self.points[stream].append(point)

        while self.times[stream][0] < time - config.GRAPH_DURATION:
            self.times[stream].pop(0)
            self.points[stream].pop(0)

        # get the min/max point in the whole data set

        values = list(self.points.values())

        if not any(values):
            min_point = 0
            max_point = 0
        else:
            min_point = min(min(v) for v in values if v)
            max_point = max(max(v) for v in values if v)

        # set the displayed range of Y axis
        self.plot.setYRange(min_point, max_point, padding=0.1)

        limit = self.parameters.param('limit').value()
        if limit != 0.0:
            # plot the warning line, using two points (start and end)
            self.warning_line.setData(
                [self.times[stream][0], self.times[stream][-1]], [limit] * 2)
            # set the red tint
            self.warning_line.setFillLevel(max_point*2)
        else:
            self.warning_line.setData([], [])
            self.warning_line.setFillLevel(0)

        # update the data curve
        self.curves[stream].setData(self.times[stream], self.points[stream])

        # round the time to the nearest GRAPH_STEP
        t = round(self.times[stream][-1] / config.GRAPH_STEP) * config.GRAPH_STEP
        self.plot.setXRange(t - config.GRAPH_DURATION + config.GRAPH_STEP,
                            t + config.GRAPH_STEP, padding=0)

        # For the numerical readout label
        self.data = float(point)
        self.numRead.setText(f"{self.data:.6f}")


    @staticmethod
    def get_name():
        return "Standard Display Item"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.plot.close()
        self.widget.close()


from publisher import publisher
from pyqtgraph.Qt.QtWidgets import QGridLayout, QLabel
from pyqtgraph.parametertree.parameterTypes import ListParameter
from pyqtgraph.Qt.QtGui import QFont
from pyqtgraph.Qt.QtCore import Qt, QTimer
import pyqtgraph as pg
import numpy as np
from .dashboard_item import DashboardItem
import config
from .registry import Register
from .series_parameter import SeriesListParameter

EXPIRED_TIME = 1.2  # time in seconds after which data "expires"

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
        self.parameters.param('num-decimals').sigValueChanged.connect(self.on_decimal_change)
        self.parameters.param('display-sparkline').sigValueChanged.connect(self.on_display_sparkline_change)
    

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(int(EXPIRED_TIME * 1000))

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

        # Big numerical readout
        self.numRead = QLabel("Not Connected")
        self.decimals = 2
        
        label_font = QFont()
        label_font.setPointSize(15)
        self.label.setFont(label_font)
        num_read_font = QFont()
        num_read_font.setPointSize(15)
        self.numRead.setFont(num_read_font)

        
        self.layout.addWidget(self.label, 0, 0)
        self.layout.addWidget(self.numRead, 0, 1)
        self.layout.addWidget(self.widget, 1, 0, 1, 2)
        self.numRead.setAlignment(Qt.AlignCenter)
        
        self.resize(300,100)
        self.show_size = self.size()
        self.hide_size = self.size()
        
        self.on_label_change(self.parameters.param('label'), self.parameters.param('label').value())

    def add_parameters(self):
        text_param = {'name': 'label', 'type': 'str', 'value': ''}
        series_param = SeriesListParameter()
        limit_param = {'name': 'limit', 'type': 'float', 'value': 0.0}
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0.0}
        show_slope_param = {'name': 'Show Slope of Linear Approx.', 'type': 'bool', 'value': False}
        font_size_param = {'name': 'font-size', 'type': 'int', 'value': 15, 'limits': (10, 30)}
        num_decimals_param = {'name': 'num-decimals', 'type': 'int', 'value': 2, 'limits': (0, 6)}
        display_sparkline_param = {'name': 'display-sparkline', 'type': 'bool', 'value': True}
        return [text_param, series_param, limit_param, offset_param, display_sparkline_param, font_size_param, num_decimals_param,show_slope_param]
    
    def _calculate_slope(self, times: list[float], points: list[float]) -> float:
        if len(times) < 2 or len(points) < 2:
            return np.nan
        x = np.array(times, dtype=np.float64)
        y = np.array(points, dtype=np.float64)
        # Use Polynomial.fit to fit a linear polynomial (degree=1)
        p = np.polynomial.Polynomial.fit(x, y, deg=1)
        # The slope is the coefficient of the linear term
        return p.convert().coef[1]
    
    
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

    def on_decimal_change(self, param, value):
        self.decimals = value

    def on_display_sparkline_change(self, param, value):
        if value:
            self.hide_size = self.size()
            self.widget.show()
            self.resize(self.show_size)
        else:
            self.show_size = self.size()
            self.widget.hide()
            self.resize(self.hide_size)

    # Create the plot item
    def create_plot(self):
        plot = pg.PlotItem(left="Data", bottom="Seconds")
        plot.setMenuEnabled(False)     # hide the default context menu when right-clicked
        plot.setMouseEnabled(x=False, y=False)
        plot.hideButtons()
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

        # Filter out the points that are in the series
        values = [ self.points[v] for v in self.points.keys() if v in self.series]
        
        # get the min/max point in the whole data set
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
        if self.parameters.param('Show Slope of Linear Approx.').value():
            slope_values: list[str] = []
            for stream in self.series:
                slope = self._calculate_slope(self.times[stream], self.points[stream])
                slope_values.append(f"{slope:.2f}" if not np.isnan(slope) else "[--]")
            slope_text = " Slope: " + ", ".join(slope_values)
            self.numRead.setText(f"Point: {self.data:.{self.decimals}f}{slope_text}")
        else:
            slope_text = ""
            self.numRead.setText(f"{self.data:.{self.decimals}f}")
        # Restart timer
        self.setStyleSheet("")
        self.expired_timeout.stop()
        self.expired_timeout.start(int(EXPIRED_TIME * 1000))

    def expire(self):
        self.setStyleSheet("color: red")

    @staticmethod
    def get_name():
        return "Standard Display Item"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.plot.close()
        self.widget.close()
        super().on_delete()


from publisher import publisher
from pyqtgraph.Qt.QtWidgets import QGridLayout
import pyqtgraph as pg
import numpy as np
from .dashboard_item import DashboardItem
import config
from .registry import Register
from .series_parameter import SeriesChecklistParameter


@Register
class PlotDashItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        self.last = {}

        # storing the series name as key, its time and points as value
        # since each PlotDashItem can contain more than one curve
        self.times = {}
        self.points = {}

        # Specify the layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.parameters.param('offset').sigValueChanged.connect(self.on_offset_change)
    
        self.series = self.parameters.param('series').value()
        # just a single global offset for now
        self.offset = self.parameters.param('offset').value()
    

        # subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # a default color list for plotting multiple curves
        # black blue magenta green cyan white
        self.color = ['k', 'b', 'm', 'g', 'c', 'w']

        # create the plot
        self.plot = self.create_plot()

        # create the plot widget
        self.widget = pg.PlotWidget(plotItem=self.plot)

        # add it to the layout
        self.layout.addWidget(self.widget, 0, 0)

    def add_parameters(self):
        series_param = SeriesChecklistParameter()
        limit_param = {'name': 'limit', 'type': 'float', 'value': 0}
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0}
        show_slope_param = {'name': 'Show Slope of Linear Approx.', 'type': 'bool', 'value': False}
        return [series_param, limit_param, offset_param, show_slope_param]
    
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
        if len(value) > 6:
            self.parameters.param('series').setValue(value[:6])
        self.series = self.parameters.param('series').childrenValue()
        # resubscribe to the new streams
        publisher.unsubscribe_from_all(self.on_data_update)
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)
        # recreate the plot with new series and add it to the layout
        self.plot = self.create_plot()
        self.widget = pg.PlotWidget(plotItem=self.plot)
        self.layout.addWidget(self.widget, 0, 0)
        self.resize(self.parameters.param('width').value(),
                    self.parameters.param('height').value())

    def on_offset_change(self, _, offset):
        self.offset = offset

    # Create the plot item
    def create_plot(self):
        plot = pg.PlotItem(title=f"<div style='font-size: 16pt;'><br/><b>{' / '.join(self.series)}</b><br/></div>", left="Data", bottom="Seconds")
        plot.setMenuEnabled(False)     # hide the default context menu when right-clicked
        plot.setMouseEnabled(x=False, y=False)
        plot.hideButtons()
        plot.setMinimumSize(300, 200)
        if (len(self.series) > 1):
            plot.addLegend()
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
        # if Show Slope can be activated
        if len(self.series) > 2:
            self.parameters.param('Show Slope of Linear Approx.').setValue(False)
            self.parameters.param('Show Slope of Linear Approx.').setOpts(enabled=False)
        else:
            self.parameters.param('Show Slope of Linear Approx.').setOpts(enabled=True)
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
        if limit != 0:
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

        series_name: str  = ""
        # data series name
        series_name += " / ".join(self.series) # join all data series on plot

        # value readout in the title for at most 2 series
        current_values: str = ""
        if len(self.series) <= 2:
            # avg values
            current_values += "Current: "
            last_values = [self.points[item][-1]
                           if self.points[item] else 0 for item in self.series]
            for v in last_values:
                current_values += f"[{v: < 4.4f}] "
        if self.parameters.param('Show Slope of Linear Approx.').value():
            slope_values: list[str] = []
            for stream in self.series:
                slope = self._calculate_slope(self.times[stream], self.points[stream])
                slope_values.append(f"[{slope:.2f}]")
            current_values += f"    Slope (/sec): {' '.join(slope_values)} "

        # 100 CHARS MAX for title
        series_name = f"{series_name[:100]}..." if len(series_name) > 100 else series_name

        self.plot.setTitle(title=f"<div style='font-size: 16pt;'><br/><b>{series_name}</b><br/>{current_values}</div>")

    @staticmethod
    def get_name():
        return "Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        super().on_delete()

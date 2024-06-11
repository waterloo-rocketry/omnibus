from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register
from pyqtgraph.Qt.QtWidgets import QVBoxLayout, QWidget, QLabel
from pyqtgraph.parametertree.parameterTypes import ChecklistParameter
import pyqtgraph as pg
from pyqtgraph.Qt.QtCore import Qt
import config
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

@Register
class StandardDisplayItem (DashboardItem):
    def __init__(self, *args):
        super().__init__(*args)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Medium text label
        self.label = QLabel("Label")
        self.label.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Big numerical readout
        self.value = QLabel("Not connected")
        self.value.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        # Sparkline plot
        self.last = {}

        # Storing the series name as key, time and points as value
        self.times = {}
        self.points = {}

        # Value detection based on plot_dah_item.py
        self.parameters.param('text').sigValueChanged.connect(self.on_label_change)
        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.parameters.param('offset').sigValueChanged.connect(self.on_offset_change)

        self.text = self.parameters.param('text').value()

        self.series = self.parameters.param('series').value()
        
        # Single global offset 
        self.offset = self.parameters.param('offset').value()


        # Subscribe to stream dictated by properties
        for series in self.series:
            publisher.subscribe(series, self.on_data_update)

        # Default color list for plotting multiple curves
        self.color = ['k', 'g', 'c', 'w', 'b', 'm']

        # Create Sparkline plot
        self.SparkLine = self.create_sparkline()
        self.SparkLine_widget = pg.PlotWidget(plotItem = self.SparkLine)
        

        # Add Sparkline to layout
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.SparkLine_widget)
        self.layout.addWidget(self.value)

        
        

        self.resize(300,100)
        

    def add_parameters(self):
        text_param = {'name': 'text', 'type': 'str', 'value': ''}
        series_param = ChecklistParameter(name='series',
                                          type='list',
                                          value=[],
                                          limits=publisher.get_all_streams())
        limit_param = {'name': 'limit', 'type': 'float', 'value': 0}
        offset_param = {'name': 'offset', 'type': 'float', 'value': 0}
        return [text_param, series_param, limit_param, offset_param]
    
    def on_label_change(self, param, value):
        self.text = value
        self.label.setText(self.text)

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

    # Create the sparkline plot item 
    def create_sparkline(self):
        sparkline = pg.PlotItem()
        sparkline.setMenuEnabled(False)
        sparkline.setMouseEnabled(x = False, y = False)
        sparkline.hideButtons()
        sparkline.showAxis('left', False)
        sparkline.showAxis('bottom', False)
        sparkline.setMaximumHeight(50)
        self.sparkline_curves = {}

        for i, series in enumerate(self.series):
            curve = sparkline.plot([], [], pen = self.color[i])
            self.sparkline_curves[series] = curve
        
        return sparkline
    
    # def on_data_update(self, stream, payload):
    #     time, point = payload

    #     point += self.offset

    #     if time - self.last[stream] < 1 / config.GRAPH_RESOLUTION:
    #         return 
        
    #     self.last[stream] = time 

    #     self.times[stream].append(time)
    #     self.points[stream].append(point)

    #     while self.time[stream][0] < time - config.GRAPH_DURATION:
    #         self.times[stream].pop(0)
    #         self.points[stream].pop(0)
        
    #     values = list(self.points.values())

    #     if not any(values):
    #         min_point = 0
    #         max_point = 0

    #     else:
    #         min_point = min(min(v) for v in values if v)
    #         max_point = max(max(v) for v in values if v)

    #     # Update the data curve for sparkline plot
    #     self.sparkline_curves[stream].setData(self.times[stream], self.points[stream])

    #     # Title for sparkline plot
    #     self.sparkline.setTitle("/".join(self.series))        

    def on_data_update(self, stream, payload):
        time, point = payload
        self.data = float(point)
        self.value.setText(f"{self.data:.6f}")

    @staticmethod
    def get_name():
        return "Standard Display Item"
    
    def on_delete(self):
        publisher.unsusbcribe_from_all(self.on_data_update)
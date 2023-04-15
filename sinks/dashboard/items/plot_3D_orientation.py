from publisher import publisher
from pyqtgraph.Qt.QtWidgets import QBoxLayout
from pyqtgraph.parametertree.parameterTypes import ListParameter
import pyqtgraph.opengl as gl
from sinks.dashboard.items.dashboard_item import DashboardItem
import numpy as np
from .registry import Register


@Register
class Orientation3DDashItem (DashboardItem):
    def __init__(self, params=None):
        # Call this in **every** dash item constructor
        super().__init__(params)

        # Specify the layout
        self.layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.setLayout(self.layout)

        self.series = self.parameters.param('series').value()

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

        publisher.subscribe(self.series, self.on_data_update_orientation)
        self.parameters.param('series').sigValueChanged.connect(self.on_series_change)
        self.xaxis = gl.GLLinePlotItem()
        self.view.addItem(self.xaxis)
        self.yaxis = gl.GLLinePlotItem()
        self.view.addItem(self.yaxis)
        self.zaxis = gl.GLLinePlotItem()
        self.view.addItem(self.zaxis)
        self.orientation = (0, 0, 0)  # Euler Angles

        # need to set minimum dimensions because it
        # defaults to 40 for some reason
        with self.parameters.treeChangeBlocker():
            self.parameters.param('width').setValue(600)
            self.parameters.param('height').setValue(600)
        # add it to the layout
        self.layout.addWidget(self.view)

    def on_series_change(self, param, value):
        publisher.unsubscribe_from_all(self.on_data_update_orientation)
        self.series = value
        publisher.subscribe(self.series, self.on_data_update_orientation)

    def addParameters(self):
        series_param = ListParameter(name='series',
                                          type='list',
                                          default="",
                                          limits=publisher.get_all_streams())
        return [series_param]

    def on_data_update_orientation(self, stream, payload):
        time, orientation = payload

        xlist = [(0, 0, 0), self.transform((10, 0, 0), orientation)]
        ylist = [(0, 0, 0), self.transform((0, 10, 0), orientation)]
        zlist = [(0, 0, 0), self.transform((0, 0, 10), orientation)]

        self.xaxis.setData(pos=np.array(xlist), color=(1.0, 0.0, 0.0, 1.0))
        self.yaxis.setData(pos=np.array(ylist), color=(0.0, 1.0, 0.0, 1.0))
        self.zaxis.setData(pos=np.array(zlist), color=(0.0, 0.0, 1.0, 1.0))

    def transform(self, point, euler_angle):
        """
        This function applies a Euler Angle to a point
        using 3 rotation matricies. The specifics can be found
        here

        https://mathworld.wolfram.com/EulerAngles.html
        """
        return self.Rx(self.Ry(self.Rz(point, euler_angle[0]), euler_angle[1]), euler_angle[2])

    def Rz(self, point, gamma):
        """
        Apply a rotation of gamma radians about
        the z-axis (on the xy plane)
        """
        x, y, z = point

        return (
            np.cos(gamma)*x - np.sin(gamma)*y,
            np.sin(gamma)*x + np.cos(gamma)*y,
            z
        )

    def Ry(self, point, beta):
        """
        Apply a rotation of gamma radians about
        the y-axis (on the xz plane)
        """
        x, y, z = point

        return (
            np.cos(beta)*x + np.sin(beta)*z,
            y,
            -np.sin(beta)*x + np.cos(beta)*z
        )

    def Rx(self, point, alpha):
        """
        Apply a rotation of gamma radians about
        the x-axis (on the zy plane)
        """
        x, y, z = point

        return (
            x,
            np.cos(alpha)*y - np.sin(alpha)*z,
            np.sin(alpha)*y + np.cos(alpha)*z
        )

    @staticmethod
    def get_name():
        return "Orientation Plot"

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update_orientation)

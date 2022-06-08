import numpy as np

import config


class Series:
    """
    Stores and downsamples the datapoints of a single series
    """

    # A list containing all Dashboard items listening
    # to this series

    def __init__(self, name):
        self.observers = []
        self.name = name

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = 0
        self.times = np.zeros(self.size)
        self.points = np.zeros(self.size)
        self.sum = 0  # sum of series
        # "size" of running average
        self.avgSize = config.RUNNING_AVG_DURATION * config.GRAPH_RESOLUTION

        self.callback = None

    def add_observer(self, dashboard_item):
        self.observers.append(dashboard_item)

    def remove_observer(self, dashboard_item):
        # certainly not the fastest code 
        self.observers = [observer for observer in self.observers if observer != dashboard_item]

    def add(self, time, point):
        """
        Add a datapoint to this series.
        """

        # time should be passed as seconds, GRAPH_RESOLUTION is points per second
        if time - self.last < 1 / config.GRAPH_RESOLUTION:
            return

        if self.last == 0:  # is this the first point we're plotting?
            self.times.fill(time)  # prevent a rogue datapoint at (0, 0)
            self.points.fill(point)
            self.sum = self.avgSize * point

        self.last += 1 / config.GRAPH_RESOLUTION

        self.sum -= self.points[self.size - self.avgSize]
        self.sum += point

        # add the new datapoint to the end of each array, shuffle everything else back
        self.times[:-1] = self.times[1:]
        self.times[-1] = time
        self.points[:-1] = self.points[1:]
        self.points[-1] = point

        for observer in self.observers:
            observer.on_data_update(self)

    def get_running_avg(self):
        return self.sum / self.avgSize

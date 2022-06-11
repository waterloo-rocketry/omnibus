import numpy as np
import queue as q

import config


class Series:
    """
    Stores and downsamples the datapoints of a single series
    """

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
        self.desc = None

        self.callback = None

    def add_observer(self, dashboard_item):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        self.observers.append(dashboard_item)

    def remove_observer(self, dashboard_item):
        # certainly not the fastest code
        self.observers = [observer for observer in self.observers if observer != dashboard_item]

    def add(self, time, point, desc=None):
        """
        Add a datapoint to this series.
        """
        if desc is not None:
            self.desc = desc

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


class CanMsgSeries(Series):

    def __init__(self, name):
        self.observers = []
        self.name = name    # board_id
        self.payloadQ = q.Queue()

        self.callback = None

    def add_observer(self, dashboard_item):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        self.observers.append(dashboard_item)

    def remove_observer(self, dashboard_item):
        # certainly not the fastest code
        self.observers = [observer for observer in self.observers if observer != dashboard_item]

    def add(self, payload):
        """
        Add a new payload to this series.
        """
        self.payloadQ.put(payload)

        for observer in self.observers:
            observer.on_data_update(self)

    def get_msg(self):
        return self.payloadQ.get()

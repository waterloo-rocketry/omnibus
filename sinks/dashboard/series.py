import numpy as np

import config

class Subject:
    """
    Abstract class acting as the Subject of Observation from observers.
    """
    def __init__ (self):
        self.observers = []
        
    def add_observer(self, observer):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        self.observers.append(observer)

    def remove_observer(self, obs_to_remove):
        # certainly not the fastest code
        self.observers.remove(obs_to_remove)

    def notify_observers(self):
        for observer in self.observers:
            observer.on_data_update(self)

class Series(Subject):
    """
    Stores and downsamples the datapoints of a single series
    """

    def __init__(self, name, time_rollover=False):
        super().__init__()
        self.name = name

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = 0
        self.times = np.zeros(self.size)
        self.points = np.zeros(self.size)
        self.sum = 0  # sum of series
        # "size" of running average
        self.avgSize = config.RUNNING_AVG_DURATION * config.GRAPH_RESOLUTION
        self.desc = None
        self.time_rollover = time_rollover
        self.time_offset = 0

        self.callback = None


    def add(self, time, point, desc=None):
        """
        Add a datapoint to this series.
        """
        if desc is not None:
            self.desc = desc

        time += self.time_offset
        if self.time_rollover:
            if time < self.times[-1]:  # if we've wrapped around
                self.time_offset += self.times[-1]  # increase the amount we need to add

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
        
        self.notify_observers()

    def get_running_avg(self):
        return self.sum / self.avgSize


class CanMsgSeries(Subject):

    def __init__(self, name):
        
        super().__init__()
        self.name = name    # board_id
        self.payloadQ = []

        self.callback = None


    def add(self, payload):
        """
        Add a new payload to this series.
        """
        self.payloadQ.append(payload)

        if len(self.payloadQ) > 50:
            self.payloadQ.pop(0)
        
        self.notify_observers()

    def get_msg(self):
        return self.payloadQ[-1]

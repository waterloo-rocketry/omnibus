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
        self.callback = None

    def add(self, time, point, desc=None):
        """
        Add a datapoint to this series.
        """
        if desc is not None:
            self.desc = desc
        
        self.time = time
        self.point = point
        self.notify_observers()



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

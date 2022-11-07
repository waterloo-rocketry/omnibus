import numpy as np

import config

class Publisher:
    """
    Abstract class acting as the Subject of Observation from observers.
    """
    def __init__ (self, name, time_rollover = False):
        self.name = name
        self.callback = None
        self.observers = []
        self.time_rollover = time_rollover

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

    def add(self, payload):
        self.payload = payload
        self.notify_observers()


class Series(Publisher):
    """
    Stores and downsamples the datapoints of a single series
    """

    def __init__(self, name, time_rollover=False):
        super().__init__(name, time_rollover)

class CanMsgSeries(Publisher):

    def __init__(self, name):
        
        super().__init__(name)

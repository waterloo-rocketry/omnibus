import numpy as np

import config

class Publisher:
    """
    Abstract class acting as the Subject of Observation from observers.
    """
    def __init__ (self):
        self.series = {}

    def get_all_series(self):

    def add_serie (self, serie):
        self.series[serie] = []
    def subscribe(self, serie, observer):
        """
        An observer is a dashboard item that cares
        about data updates. Adding an observer
        means adding an item to be notified
        when the data is updated
        """
        if serie not in self.series:
            self.series[serie] = []
        self.series[serie].append(observer)

    def unsubscribe_from_all(self, observer):
        for serie in self.series:
            serie.remove(observer)

    def update(self, serie, payload):
        for observer in self.series[serie]:
            observer.on_data_update(payload)

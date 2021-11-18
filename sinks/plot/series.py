import numpy as np

import config


class Series:
    """
    Stores and downsamples the datapoints of a single series
    """
    series = []  # keep track of all initialized series

    def __init__(self, name, parser):
        self.name = name
        self.parser = parser

        self.size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
        self.last = 0
        self.downsampleCount = 0
        self.times = np.zeros(self.size)
        self.points = np.zeros(self.size)
        self.sum = 0  # sum of series
        # "size" of running average
        self.avgSize = config.RUNNING_AVG_DURATION * config.GRAPH_RESOLUTION

        self.callback = None

        Series.series.append(self)

    def register_update(self, callback):
        # called every time data is added
        self.callback = callback

    def add(self, payload):
        """
        Add the datapoint from an omnibus message payload.
        """

        parsed = self.parser.parse(payload)  # turn the message into a datapoint
        if parsed is None:  # the message didn't represent a valid datapoint
            return
        time, point = parsed

        if time - self.last < 1 / config.GRAPH_RESOLUTION:
            return
        self.last += 1 / config.GRAPH_RESOLUTION

        self.sum -= self.points[self.size - self.avgSize]
        self.sum += point

        self.points[:-1] = self.points[1:]
        self.points[-1] = point
        self.times[:-1] = self.times[1:]
        self.times[-1] = time

        if self.callback:
            self.callback()

    def get_running_avg(self):
        return self.sum / self.avgSize

    @staticmethod
    def parse(channel, payload):
        """
        Add payload to all series which subscribe to channel
        """
        for series in Series.series:
            if channel.startswith(series.parser.channel):
                series.add(payload)

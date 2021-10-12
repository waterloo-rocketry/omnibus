import numpy as np

import config


class Series:
    """
    Stores and downsamples the datapoints of a single series
    """
    series = []  # keep track of all initialized series

    def __init__(self, name, rate, parser):
        self.name = name
        self.parser = parser

        if rate > config.GRAPH_RESOLUTION:  # we need to downsample
            size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
            self.downsample = rate // config.GRAPH_RESOLUTION
        else:  # don't downsample
            size = rate * config.GRAPH_DURATION
            self.downsample = 1
        self.downsampleCount = 0
        self.times = np.zeros(size)
        self.points = np.zeros(size)
        self.first = True
        self.sum = 0 # Sum of series
        self.size = size # Size of series
        self.callback = None

        Series.series.append(self)

    def register_update(self, callback):
        # called every time data is added
        self.callback = callback

    def add(self, payload):
        """
        Add the datapoint from an omnibus message payload.
        """
        # downsample by only adding every n points
        self.downsampleCount += 1
        if self.downsampleCount != self.downsample:
            return
        self.downsampleCount = 0

        parsed = self.parser.parse(payload)  # turn the message into a datapoint
        if parsed is None:  # the message didn't represent a valid datapoint
            return
        time, point = parsed
        # fill the arrays with our first datapoint to avoid plotting (0, 0)
        if self.first:
            self.first = False
            self.times.fill(time)
            self.points.fill(point)
            self.sum += point
        else:
            self.sum -= self.points[0]
            self.sum += point
            self.points[:-1] = self.points[1:]
            self.points[-1] = point
            self.times[:-1] = self.times[1:]
            self.times[-1] = time

        if self.callback:
            self.callback()

    def getRunningAvg(self):
        return (self.sum / self.size)
    
    @staticmethod
    def parse(channel, payload):
        """
        Add payload to all series which subscribe to channel
        """
        for series in Series.series:
            if channel.startswith(series.parser.channel):
                series.add(payload)

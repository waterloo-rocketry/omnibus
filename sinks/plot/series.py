import numpy as np

import config

class Series:
    series = []
    def __init__(self, name, rate, parser):
        self.name = name
        self.parser = parser

        if rate > config.GRAPH_RESOLUTION:
            size = config.GRAPH_RESOLUTION * config.GRAPH_DURATION
            self.downsample = rate // config.GRAPH_RESOLUTION
        else:
            size = rate * config.GRAPH_DURATION
            self.downsample = 1
        self.downsampleCount = 0
        self.times = np.zeros(size)
        self.points = np.zeros(size)
        self.first = True

        self.callback = None

        Series.series.append(self)

    def registerUpdate(self, callback):
        self.callback = callback

    def add(self, payload):
        self.downsampleCount += 1
        if self.downsampleCount != self.downsample:
            return
        self.downsampleCount = 0

        parsed = self.parser.parse(payload)
        if parsed is None:
            return
        time, point = parsed
        if self.first:
            self.first = False
            self.times.fill(time)
            self.points.fill(point)
        else:
            self.points[:-1] = self.points[1:]
            self.points[-1] = point
            self.times[:-1] = self.times[1:]
            self.times[-1] = time

        if self.callback:
            self.callback()

    @staticmethod
    def parse(channel, payload):
        for series in Series.series:
            if channel.startswith(series.parser.channel):
                series.add(payload)

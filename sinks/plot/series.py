import numpy as np

class Series:
    series = []
    def __init__(self, name, rate, parser, GRAPH_RESOLUTION, GRAPH_DURATION):
        self.name = name
        self.parser = parser

        if rate > GRAPH_RESOLUTION:
            size = GRAPH_RESOLUTION * GRAPH_DURATION
            self.downsample = rate // GRAPH_RESOLUTION
        else:
            size = rate * GRAPH_DURATION
            self.downsample = 1
        self.downsampleCount = 0
        self.times = np.zeros(size)
        self.points = np.zeros(size)
        self.first = True

        Series.series.append(self)

    def add(self, payload):
        self.downsampleCount += 1
        if self.downsampleCount != self.downsample:
            return
        self.downsampleCount = 0

        time, point = self.parser.parse(payload)
        if self.first:
            self.first = False
            self.times.fill(time)
            self.points.fill(point)
        else:
            self.points[:-1] = self.points[1:]
            self.points[-1] = point
            self.times[:-1] = self.times[1:]
            self.times[-1] = time

    @staticmethod
    def parse(channel, payload):
        changed = False
        for series in Series.series:
            if channel.startswith(series.parser.channel):
                series.add(payload)
                changed = True
        return changed

from parsers import DAQParser, FillSensingParser, TemperatureParser
from series import Series

GRAPH_DURATION = 30  # size of x axis in seconds
GRAPH_RESOLUTION = 10  # data points per second


def setup():
    DAQ_SENSORS = [
        "Fake0",
        "Fake1",
        "Fake2",
        "Fake3",
        "Fake4",
        "Fake5",
        "Fake6",
        "Fake7",
    ]
    for sensor in DAQ_SENSORS:
        Series(sensor, 50, DAQParser("DAQ", sensor))
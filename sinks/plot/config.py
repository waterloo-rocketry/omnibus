from parsers import DAQParser, FillSensingParser, TemperatureParser
from series import Series

GRAPH_DURATION = 30  # size of x axis in seconds
GRAPH_RESOLUTION = 10  # data points per second


def setup():
    # DAQ_SENSORS = [
    #     "P5 (PT-5) - SRAD Vent Valve",
    #     "P4 (PT-1) - Ox Fill",
    #     "P3 (PT-2) - Ox Tank",
    #     "P2 (PT-3) - CC", "Thrust",
    #     "SP1 (PT-4) - Nozzle",
    #     "FAST", "Omega S-Type",
    #     "T8 - Tank Heating"
    # ]

    DAQ_SENSORS = ["Fake0", "Fake1", "Fake2", "Fake3", "Fake4", "Fake5", "Fake6", "Fake7"]
    for sensor in DAQ_SENSORS:
        Series(sensor, 50, DAQParser("DAQ", sensor))

    Series("Fill Sensing", 1, FillSensingParser("CAN/Parsley"))
    Series("T10 - Exit", 6, TemperatureParser("CAN/Parsley", 10))
    Series("T20 - Diverging", 3, TemperatureParser("CAN/Parsley", 20))
    Series("T21 - Throat", 3, TemperatureParser("CAN/Parsley", 21))
    Series("T30 - Reservoir", 3, TemperatureParser("CAN/Parsley", 30))
    Series("T31 - Vent", 3, TemperatureParser("CAN/Parsley", 31))

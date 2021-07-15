from parser import DAQParser
from series import Series

GRAPH_DURATION = 30 # size of x axis in seconds
GRAPH_RESOLUTION = 10 # data points per second

def setup():
  # DAQ_SENSORS = ["P5 - Pneumatics", "P4 - Ox Fill", "P3 - Ox Tank", "P2 - CC",
  #                "Thrust", "SP1 - Nozzle", "FAST", "Omega S-Type", "T8 - Tank Heating"]
  DAQ_SENSORS = [f"Fake{i}" for i in range(8)]
  for sensor in DAQ_SENSORS:
    Series(sensor, 50, DAQParser("DAQ", sensor))

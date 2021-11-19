GRAPH_DURATION = 30  # size of x axis in seconds
GRAPH_RESOLUTION = 10  # data points per second
GRAPH_STEP = GRAPH_DURATION / 60  # how often to shift the graphs left in seconds.
# last n seconds to be accounted for in running average, please don't set it larger than GRAPH_DURATION
RUNNING_AVG_DURATION = 2

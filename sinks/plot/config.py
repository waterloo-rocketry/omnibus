GRAPH_DURATION = 30  # size of x axis in seconds
GRAPH_RESOLUTION = 10  # data points per second
GRAPH_STEP = GRAPH_DURATION / 60  # how often to shift the graphs left in seconds.
# last n seconds to be accounted for in running average, please don't set it larger than GRAPH_DURATION
RUNNING_AVG_DURATION = 2
WINDOW_SIZE_X = 1000
WINDOW_SIZE_Y = 600
DOCK_SIZE_X = 200
DOCK_SIZE_Y = 200
ITEMS_PER_ROW = WINDOW_SIZE_X // DOCK_SIZE_X
ITEMS_PER_COLUMN = WINDOW_SIZE_Y // DOCK_SIZE_Y

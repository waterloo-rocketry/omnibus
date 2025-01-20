from omnibus import Receiver

# import parsers
from interamap import interamap_driver

receiver = Receiver("")  # subscribe to all channels

interamap_driver()

# Generates logged message and saves to

import logging

from omnibus import Receiver

# Set to listen to all channels -> ""
channel = ""
receiver = Receiver("temp.server", channel)

# name of the file the log is saved to
fname = 'globalLog.log'
# creates a new logger
logger = logging.getLogger("global")
# sets minimum logging level that will be recorded
# the priorities from lowest to highest is: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.INFO)
# configures the logger to log into a designated file
fileHdlr = logging.FileHandler(fname)
fileHdlr.setLevel(logging.INFO)
# generate formatting of logged messages
# ex: "January 1, 2021, 00:00:00 : INFO : channel1 : Something went wrong."
formatter = logging.Formatter('%(ts)s :: %(msgChannel)s :: %(levelname)s :: %(message)s')
fileHdlr.setFormatter(formatter)
logger.addHandler(fileHdlr)

while True:
    msg = receiver.recv_message()
    ts = msg.timestamp
    msgChannel = msg.channel
    # logs the message as info level
    logging.info(msg.payload)

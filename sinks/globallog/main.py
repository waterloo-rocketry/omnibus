# Generates logged message and saves to globalLog.log

import logging

from omnibus import Receiver

# Set to listen to all channels -> ""
channel = ""
receiver = Receiver("tcp://localhost:5076", channel)

msg = receiver.recv_message()

# name of the file the log is saved to
fname = 'globalLog.log'
# creates a new logger
logger = logging.getLogger("global")
# sets minimum logging level that will be recorded
# the priorities from lowest to highest is: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.setLevel(logging.DEBUG)
# adds filehandler to the logger to log into a designated file
fileHdlr = logging.FileHandler(fname)
fileHdlr.setLevel(logging.DEBUG)
# generate formatting of logged messages
# ex: "68464665.21550 : INFO : fake : [123123,123]"
formatter = logging.Formatter('%(timestamp)s :: %(channel)s :: %(levelname)s :: %(message)s')
fileHdlr.setFormatter(formatter)
logger.addHandler(fileHdlr)

while True:
    msg = receiver.recv_message()
    # logs the message as info level
    logger.info(msg.payload, extra={'timestamp': msg.timestamp, 'channel': msg.channel})

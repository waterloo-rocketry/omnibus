# Generates loggers based on channel passed to log
import logging

def log(channel, fname = 'globalLog.log'):
    """
    Return a new logger

    Parameters
    ----------

    channel: str
        The channel the message on the bus is being passed through.

    fname: file name
        The file name the log is saved to, if there are no existing file in the directory it will create one

    Returns a working logger

    For example:
        # inside somewhere.py (from logger import log)
        logChannel1 = log("channel1", "channel1.log")
        log.debug("test!)
        ...
    """
    # creates a new logger
    logger = logging.getLogger(channel)
    # sets minimum logging level that will be recorded
    # the priorities from lowest to highest is: DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger.setLevel(logging.WARNING)
    # configures the logger to log into a designated file
    fileHdlr = logging.FileHandler(fname)
    fileHdlr.setLevel(logging.WARNING)
    # change formatting of logged messages
    # ex: "2019-02-17 12:40:14,797 : WARNING : channel1 : Something went wrong."
    format = logging.Formatter('%(asctime)s :: %(channel)s :: %(levelname)s :: %(message)s')
    fileHdlr.setFormatter(format)
    logger.addHandler(fileHdlr)
    return logger

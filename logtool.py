import logging
import os
# dynamically generates logger objects and log files based on the number of sources and sinks and stores all loggers in a dictionary accessed with the filename without .py
# so for example the file "sinks/dashboard/main.py" would be accessed with "dashboard"


def init_loggers():
    # initializes variable to be returned
    loggers = dict([])

    # generates logger objects and log files for each source
    for filename in os.listdir("sources"):
        os.makedirs(os.path.dirname(f'logs/sources/{filename}.log'), exist_ok=True)
        logger = logging.getLogger(filename)
        logger.setLevel("INFO")

        handler = logging.FileHandler(f"logs/sources/{filename}.log", mode='w')
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        loggers.update({filename: logger})

    # generates logger objects and log files for each sink
    for filename in os.listdir("sinks"):
        os.makedirs(os.path.dirname(f'logs/sinks/{filename}.log'), exist_ok=True)
        logger = logging.getLogger(filename)
        logger.setLevel("INFO")

        handler = logging.FileHandler(f"logs/sinks/{filename}.log", mode='w')
        formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        loggers.update({filename: logger})

    # generates a misc logger and log file in case there is an output or error from neither a sink nor a source
    os.makedirs(os.path.dirname(f'logs/other.log'), exist_ok=True)
    logger = logging.getLogger("other")
    logger.setLevel("INFO")

    handler = logging.FileHandler(f"logs/other.log", mode='w')
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    loggers.update({"other": logger})

    return loggers

import logging
import os
# dynamically generates logger objects and log files based on the number of sources and sinks and stores all loggers in a dictionary accessed with the filename without .py
# so for example the file "sinks/dashboard/main.py" would be accessed with "dashboard"


def init_loggers(source_path, sink_path):
    # initializes variable to be returned
    loggers = dict([])
    source = source_path.split("/")[-1]
    sink = sink_path.split("/")[-1]

    # generates logger objects and log files for each source
    os.makedirs(os.path.dirname(f'logs/sources/{source}.log'), exist_ok=True)
    logger = logging.getLogger(source)
    logger.setLevel("INFO")

    handler = logging.FileHandler(f"logs/sources/{source}.log", mode='w')
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    loggers.update({source: logger})

    # generates logger objects and log files for each sink
    os.makedirs(os.path.dirname(f'logs/sinks/{sink}.log'), exist_ok=True)
    logger = logging.getLogger(sink)
    logger.setLevel("INFO")

    handler = logging.FileHandler(f"logs/sinks/{sink}.log", mode='w')
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    loggers.update({sink: logger})

    # generates a core-library logger and log file in case there is an output or error from neither a sink nor a source
    os.makedirs(os.path.dirname(f'logs/core-library.log'), exist_ok=True)
    logger = logging.getLogger("core")
    logger.setLevel("INFO")

    handler = logging.FileHandler(f"logs/core-library.log", mode='w')
    formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    loggers.update({"core": logger})

    return loggers

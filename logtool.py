import logging
import os

# Dynamically generates logger objects and log files based on the number of sources and sinks and stores all loggers in a dictionary accessed with the filename without .py
# so for example the file "sinks/dashboard/main.py" would be accessed with "dashboard"


class Logger():

    def __init__(self):
        self.loggers = dict([])
        self.add_logger(core=True)

    # Function to add a logger to the dictionary
    # core=True is only for innitializing the loggers for launcher.py
    def add_logger(self, filepath=None, core=False):
        if core == False:
            file_ref = filepath.split("/")
            file_name, file_dir = file_ref[-1], file_ref[-2]
        else:
            file_name, file_dir = "core_library", ""
        os.makedirs(os.path.dirname(f'logs/{file_dir}/{file_name}.log'), exist_ok=True)
        logger = logging.getLogger(file_name)
        logger.setLevel("INFO")

        handler = logging.FileHandler(f"logs/{file_dir}/{file_name}.log", mode='w')
        formatter = logging.Formatter('%(levelname)s:%(name)s:\n%(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        self.loggers.update({file_name: logger})

    # Logs output from a process with its respective logger, or core if it is from core-library
    def log_output(self, process, output):
        if process.args[-1] == "omnibus":
            self.loggers["core_library"].info(f"From{process.args}:{output}")
        else:
            self.loggers[process.args[1].split("/")[1]].info(f"From {process.args}:{output}")
        print(f"Output from {process.args} logged")

    # Logs output from a process with its respective logger, or core if it is from core-library
    def log_error(self, process, err):
        if process.args[-1] == "omnibus":
            self.loggers["core_library"].error(f"From{process.args}:{err}")
        else:
            self.loggers[process.args[1].split("/")[1]].error(f"From {process.args}:{err}")
        print(f"Error from {process.args} logged")

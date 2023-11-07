import logging
import os

# dynamically generates logger objects and log files based on the number of sources and sinks and stores all loggers in a dictionary accessed with the filename without .py
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
            os.makedirs(os.path.dirname(f'logs/{file_dir}/{file_name}.log'), exist_ok=True)
            logger = logging.getLogger(file_name)
            logger.setLevel("INFO")

            handler = logging.FileHandler(f"logs/{file_dir}/{file_name}.log", mode='w')
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            self.loggers.update({file_name: logger})
        else:
            os.makedirs(os.path.dirname('logs/core-library.log'), exist_ok=True)
            logger = logging.getLogger("core")
            logger.setLevel("INFO")

            handler = logging.FileHandler("logs/core-library.log", mode='w')
            formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')
            handler.setFormatter(formatter)

            logger.addHandler(handler)
            self.loggers.update({"core": logger})
    
    # Logs output from a process with its respective logger, or core if it is from core-library
    def log_output(self, process, output):
        try:
            self.loggers[process.args[-1].split("/")[1]].info(f"From {process.args}:{output}")
            print(f"\nOutput from {process.args} logged")
        except (IndexError, KeyError):
            print(f"\nOutput from {process.args} logged in core-library.log")
            self.loggers["core"].info(f"From{process.args}:{output}")
    
    # Logs output from a process with its respective logger, or core if it is from core-library
    def log_error(self, process, err):
        try:
            self.loggers[process.args[-1].split("/")[1]].error(f"From {process.args}:{err}")
            print(f"\nError from {process.args} logged")
        except (IndexError, KeyError):
            print(f"\nError from {process.args} logged in core-library.log")
            self.loggers["core"].error(f"From{process.args}:{err}")

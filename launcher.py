import os
import signal
import subprocess
import sys
import time
import argparse
import sys
import logging
from logtool import Logger
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt.QtWidgets import QApplication, QDialog, QLabel, QComboBox, QDialogButtonBox, QVBoxLayout

# Some specific commands are needed for Windows vs macOS/Linux
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP
    python_executable = "venv/Scripts/python"
else:
    python_executable = "python"

# Blank exception just for processes to throw
class Finished(Exception):
    pass

# CLI Launcher
class Launcher():
    def __init__(self) -> None:
        super().__init__()
        self.commands = []

        # Parse folders for sources and sinks
        self.modules = {"sources" : os.listdir('sources'), "sinks" : os.listdir('sinks')}
    
        # Remove dot files
        for module in self.modules.keys():
            for item in self.modules[module]:
                if item.startswith("."):
                    self.modules[module].remove(item)
    
    # Print list of sources and sinks
    def print_choices(self):
        for module in self.modules.keys():
            print(f"{module.capitalize()}:")
            for i, item in enumerate(self.modules[module]):
                print(f"\t{i+1}. {item.capitalize()}")

    # Enter inputs for CLI launcher
    def input(self):
        # Construct CLI commands to start Omnibus
        self.source_selection = int(input(f"\nPlease enter your Source choice [1-{len(self.modules['sources'])}]: ")) - 1
        self.sink_selection = int(input(f"Please enter your Sink choice [1-{len(self.modules['sinks'])}]: ")) - 1
        self.omnibus = [python_executable, "-m", "omnibus"]
        self.source = [python_executable, f"sources/{self.modules['sources'][self.source_selection]}/main.py"]
        self.sink = [python_executable, f"sinks/{self.modules['sinks'][self.sink_selection]}/main.py"]

commands=[]

if srcSelected:
    omnibus = [python_executable, "-m", "omnibus"]
    for selection in srcSelected:
        source=[python_executable, f"sources/{modules['sources'][selection - 1]}/main.py"]
        commands.append([omnibus, source]) #no need to keep appending omnibus here, only needs to run once 
    #find out more on how this command thing works 
if sinkSelected:
    for selection in sinkSelected:
        sink = [python_executable, f"sinks/{modules['sinks'][selection - 1]}/main.py"]
        commands.append([sink])
#omnibus = [python_executable, "-m", "omnibus"]
#source = [python_executable, f"sources/{modules['sources'][int(source_selection) - 1]}/main.py"]
#sink = [python_executable, f"sinks/{modules['sinks'][int(sink_selection) - 1]}/main.py"]
#commands = [omnibus, source, sink]
processes = []
print("Launching... ", end="")


#if source_selection !="0":
    #omnibus = [python_executable, "-m", "omnibus"]
    #source = [python_executable, f"sources/{modules['sources'][int(source_selection) - 1]}/main.py"]
    #commands = [omnibus, source]

#if sink_selection !='0':
    #sink = [python_executable, f"sinks/{modules['sinks'][int(sink_selection) - 1]}/main.py"]
    #commands.append(sink)



processes = [] 
print("Launching... ", end="")

    # Execute commands as subprocesses
    def subprocess(self):
        self.processes = []
        print("Launching... ", end="")
        for command in self.commands:
            if sys.platform == "win32":
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                        creationflags=CREATE_NEW_PROCESS_GROUP)
                time.sleep(0.5)
            else:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(0.5)
            self.processes.append(process)

        print("Done!")
    
    # Create loggers
    def logging(self):
        self.logger = Logger()
        self.logger.add_logger(f"sources/{self.modules['sources'][int(self.source_selection)]}")
        self.logger.add_logger(f"sinks/{self.modules['sinks'][int(self.sink_selection)]}")
        print("Loggers Initiated")

    # If any file exits or the user presses control + c,
    # terminate all other files that are running
    def terminate(self):
        try:
            while True:
                for process in self.processes:
                    if process.poll() != None:
                        raise Finished
        except (Finished, KeyboardInterrupt, Exception):
            for process in self.processes:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    process.send_signal(signal.SIGINT)

        # Dump output and error (if exists) from every
        # process to the shell 
        output, err = process.communicate()
        output, err = output.decode(), err.decode()
        print(f"\nOutput from {process.args}:")
        print(output)

        if err and "KeyboardInterrupt" not in err:
            logger.log_error(process, err)
            
    logging.shutdown()
finally:
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)

'''
Questions:
-how does the launcher work? is it able to run independently on its own? 
-how does the user select more than one sources/sink 
'''
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
from pyqtgraph.Qt.QtWidgets import (
    QApplication, QDialog, QLabel, QComboBox, QDialogButtonBox, QVBoxLayout,
    QWidget
)

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
        #self.source_selection = int(input(f"\nPlease enter your Source choice [1-{len(self.modules['sources'])}]: ")) - 1
        #self.sink_selection = int(input(f"Please enter your Sink choice [1-{len(self.modules['sinks'])}]: ")) - 1
        
        #source selection
        while True:
            self.source_selection = input(f"\nPlease enter your Source choices [1-{len(self.modules['sources'])}] separated by spaces: ")

            # Split the input string into individual values
            self.sources = self.source_selection.split()

            # Validate each input value
            valid_src = True
            self.srcSelected = []
            for src in self.sources:
                if not src.isdigit():
                    print(f"Invalid input: '{src}' is not a number.")
                    valid_src = False
                    break
                
                src = int(src)
                if 1 <= src <= len(self.modules['sources']):
                    self.srcSelected.append(src)
                else:
                    print(f"Please enter a number between 1 and {len(self.modules['sources'])}.")
                    valid_input = False
                    break
                
            if valid_src:
                break
        
        #sink selection
        while True:
            self.sink_selection = input(f"\nPlease enter your Source choices [1-{len(self.modules['sinks'])}] separated by spaces: ")
        
            # Split the input string into individual values
            self.sinks = self.sink_selection.split()
        
            # Validate each input value
            valid_sink = True
            self.sinkSelected = []
            for sink in self.sinks:
                if not sink.isdigit():
                    print(f"Invalid input: '{sink}' is not a number.")
                    valid_sink = False
                    break
                
                sink = int(sink)
                if 1 <= sink <= len(self.modules['sinks']):
                    self.sinkSelected.append(sink)
                else:
                    print(f"Please enter a number between 1 and {len(self.modules['sinks'])}.")
                    valid_sink = False
                    break
                
            if valid_sink:
                break
        
        
        
        self.commands=[]
        self.omnibus = [python_executable, "-m", "omnibus"]
        self.commands.append(self.omnibus)
        if self.srcSelected:
            for selection in self.srcSelected:
                source=[python_executable, f"sources/{self.modules['sources'][selection - 1]}/main.py"]
                #logger.add_logger(f"sources/{modules['sources'][selection - 1]}")
                self.commands.append(source)

        if self.sinkSelected:
            for selection in self.sinkSelected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection) - 1]}/main.py"]
                #logger.add_logger(f"sinks/{modules['sinks'][selection - 1]}")
                self.commands.append(sink)

        #self.source = [python_executable, f"sources/{self.modules['sources'][self.source_selection]}/main.py"]
        #self.sink = [python_executable, f"sinks/{self.modules['sinks'][self.sink_selection]}/main.py"]

        #self.commands = [self.omnibus, self.source, self.sink]

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
        #self.logger.add_logger(f"sources/{self.modules['sources'][int(self.source_selection)]}")
        #self.logger.add_logger(f"sinks/{self.modules['sinks'][int(self.sink_selection)]}")
        
        for src in self.srcSelected:
            self.logger.add_logger(f"sources/{self.modules['sources'][src - 1]}")
        
        for sink in self.sinkSelected:
            self.logger.add_logger(f"sinks/{self.modules['sinks'][sink - 1]}")

        
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
                # process to the coresponding log file
                output, err = process.communicate()
                output, err = output.decode(), err.decode()
                
                # Log outputs
                self.logger.log_output(process, output)

                # Log errors
                if err and "KeyboardInterrupt" not in err:
                    self.logger.log_error(process, err)
                    
            logging.shutdown()
        finally:
            for process in self.processes:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    process.send_signal(signal.SIGINT) 

#class for the checkable combo box that allows multiple input selection
class CheckableComboBox(QWidget, Launcher):
    def __init__(self, modules):
        super().__init__()
        layout=QVBoxLayout()

        #list for sources 
        self.srcList=QComboBox()
        self.srcList.setEditable(True)
        self.srcList.setMaxVisibleItems(5) #does this enable the scrolling on the list
        self.srcList.view().pressed.connect(self.select_item)


        #add sources/sinks to the selectable list 
        for src in modules.get("sources"):
            self.srcList.addItem(src)  

        #todo for sink if this works 
    

# GUI Launcher
class GUILauncher(Launcher, QDialog):
    def __init__(self):
        super().__init__()
        self.selected_ok = False

        # Sets window title and ensures size of dialog is fixed
        self.setGeometry(300, 300, 500, 230)
        self.setFixedSize(500, 230)
        self.setWindowTitle("Omnibus Launcher")

        # Description / Title
        description = QLabel(self)
        description.setText("Please enter your source and sink choices")
        description.setGeometry(20, 12, 400, 20)
        description.setFont(QtGui.QFont("", 18))

        # Create a source label
        source = QLabel(self)
        source.setText("Source:")
        source.setGeometry(20, 53, 150, 20)

        # Create a dropdown for source
        self.source_dropdown = QComboBox(self)
        self.source_dropdown.setGeometry(90, 52, 150, 30)

        # Add items to the sources dropdown
        for source in self.modules.get("sources"):
            self.source_dropdown.addItem(source)

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sink:")
        sink.setGeometry(20, 93, 150, 20)

        # Create a dropdown for sink
        self.sink_dropdown = QComboBox(self)
        self.sink_dropdown.setGeometry(90, 92, 150, 30)

        # Add items to the sinks dropdown
        for sink in self.modules.get("sinks"):
            self.sink_dropdown.addItem(sink)

        # Enter selections button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.construct_commands)
        self.button_box.rejected.connect(self.close)

        # Add button to layout
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def construct_commands(self):
        self.selected_ok = True

        # Selected source and sink in GUI
        self.source_selection = self.modules['sources'].index(self.source_dropdown.currentText())
        self.sink_selection = self.modules['sinks'].index(self.sink_dropdown.currentText())

        self.omnibus = ["python", "-m", "omnibus"]
        self.source = ["python", f"sources/{self.source_dropdown.currentText()}/main.py"]
        self.sink = ["python", f"sinks/{self.sink_dropdown.currentText()}/main.py"]

        self.commands = [self.omnibus, self.source, self.sink]

        self.close()
    
    def closeEvent(self, event):
        if self.selected_ok:
            event.accept()
        else:
            sys.exit()

def main():
    parser = argparse.ArgumentParser(description='Omnibus Launcher')
    parser.add_argument('--text', action='store_true', help='Use text input mode')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    # If 'python launcher.py --text' is run this block of code will execute
    if args.text:
        print("Running in text mode")
        launcher = Launcher()
        launcher.print_choices()
        launcher.input()
        launcher.subprocess()
        launcher.logging()
        launcher.terminate()

    # If 'python launcher.py' is run this this block of code will execute
    else:
        print("Running in GUI mode")
        gui_launcher = GUILauncher()
        gui_launcher.show()
        app.exec()
        gui_launcher.subprocess()
        gui_launcher.logging()
        gui_launcher.terminate()

if __name__ == '__main__':
    main()

'''

-figure out how to do multiselect for the sources/sinks for the gui
    -allow user to select source from a drop down list and add to comboBox? 
    -allow user to add/remove items from the selected list 
    -no repeated selection allowed 

    -dont need a separate class for it, just add it to the guilauncher class 


cli input:
-mostly copy and paste from launcher_old.py
-deal with the loggers 
'''
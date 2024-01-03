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
    QWidget, QCheckBox, QHBoxLayout, QGridLayout
)
from pyqtgraph.Qt.QtGui import QStandardItemModel
from pyqtgraph.Qt.QtCore import Qt


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
                self.commands.append(source)

        if self.sinkSelected:
            for selection in self.sinkSelected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection) - 1]}/main.py"]
                self.commands.append(sink)


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
        
        #different for cli and gui input

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



class GUILauncher(Launcher, QDialog):
    def __init__(self):
        super().__init__()
        self.selected_ok = False

        self.setGeometry(300, 300, 500, 230)
        self.setFixedSize(500, 400)
        self.setWindowTitle("Omnibus Launcher")

        #description = QLabel(self)
        #description.setText("Please enter your source and sink choices")
        #description.setGeometry(20, 5, 500, 50)
        #description.setFont(QtGui.QFont("", 18))

        source_label = QLabel(self)
        source_label.setText("Sources:")
        source_label.setGeometry(20, 53, 150, 20)

        # Create checkboxes for each source option
        self.srcCheckBoxes = [QCheckBox(f"{i+1}. {src}") for i, src in enumerate(self.modules.get("sources"))]
        self.srcSelected=[]
        # Layout for source checkboxes
        self.srcLayout = QGridLayout()
        row = 0
        col = 0
        for checkbox in self.srcCheckBoxes:
            self.srcLayout.addWidget(checkbox, row, col)
            col += 1
            if col == 3:  # Three checkboxes per row
                col = 0
                row += 1

        sourceList = QWidget()
        sourceList.setLayout(self.srcLayout)

        #connect checkbox state to signals to detect which sources were selected 
        for checkbox in self.srcCheckBoxes:
            checkbox.stateChanged.connect(self.update_selected)

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sinks:")
        sink.setGeometry(20, 93, 150, 20)

       #create checkboxes for each sink option 
        self.sinkCheckBoxes=[QCheckBox(f"{i+1}. {sink}") for i, sink in enumerate(self.modules.get("sinks"))]
        self.sinkSelected=[]
        #Layout for sink checkboxes
        self.sinkLayout=QGridLayout()
        row=0
        col=0
        for checkbox in self.sinkCheckBoxes:
            self.sinkLayout.addWidget(checkbox, row, col)
            col+=1
            if col==3:
                col=0
                row+=1
        sinkList=QWidget()
        sinkList.setLayout(self.sinkLayout)

        #connect checkbox state to signals to detect which sources were selected 
        for checkbox in self.sinkCheckBoxes:
            checkbox.stateChanged.connect(self.update_selected)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self.button_box.accepted.connect(self.construct_commands)
        self.button_box.rejected.connect(self.close)

        main_layout = QVBoxLayout()
        #main_layout.addWidget(description)
        main_layout.addWidget(source_label)
        main_layout.addWidget(sourceList)  # Add source checkboxes in grid layout
        main_layout.addWidget(sink)
        main_layout.addWidget(sinkList)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)  # Set the main layout for the dialog

    def construct_commands(self):
        self.selected_ok = True
        
        self.omnibus = ["python", "-m", "omnibus"]
        self.commands.append(self.omnibus)

        
        if self.srcSelected:
            for selection in self.srcSelected:
                source=[python_executable, f"sources/{self.modules['sources'][int(selection)-1]}/main.py"]
                self.commands.append(source)
                
        if self.sinkSelected:
            for selection in self.sinkSelected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection)-1]}/main.py"]
                self.commands.append(sink)
        self.close()

    def update_selected(self, state):
        checkbox=self.sender()
        text=checkbox.text()
        index=text.split('. ')[0]

        if checkbox in self.srcCheckBoxes:
            selectedList=self.srcSelected
        else:
            selectedList=self.sinkSelected
        if checkbox.isChecked():
            
            if index not in selectedList:
                selectedList.append(int(index))
                
        else:
            selectedList.remove(int(index))
        
    
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
You can probably remove the Please enter your source and sink choices text [DONE]
Pluralize Source: and Sink: [DONE]
Remove the extra spacing under the source and sink headings
Remove the numbers for the sources and sinks listed
Capitalize the sources and sinks listed
'''
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
    QApplication, QDialog, QLabel, QDialogButtonBox, QVBoxLayout,
    QWidget, QCheckBox, QGridLayout
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
        self.src_selected = []
        self.sink_selected = []
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

        #Source selection
        self.src_selected = self.validate_inputs(self.modules['sources'], "Source")

        #Sink selection 
        self.sink_selected = self.validate_inputs(self.modules['sinks'], "Sink")

        self.omnibus = [python_executable, "-m", "omnibus"]
        self.commands.append(self.omnibus)
        if self.src_selected:
            for selection in self.src_selected:
                source=[python_executable, f"sources/{self.modules['sources'][selection - 1]}/main.py"]
                self.commands.append(source)

        if self.sink_selected:
            for selection in self.sink_selected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection) - 1]}/main.py"]
                self.commands.append(sink)

    #validate the input selection for cli input
    def validate_inputs(self, choices, module):
        while True:
            user_input = input(f"\nPlease enter your {module} choices [1-{len(choices)}] separated by spaces: ")

            #split the input string into individual values
            selection = user_input.split()

            #validate the input 
            valid_input = True
            selected_indices = []

            for item in selection:
                #Check if the input is a number
                if not item.isdigit():
                    print(f"Invalid input: '{item}' is not a number.")
                    valid_input = False
                    break
                
                #Check if the index is within the choice range 
                index = int(item)
                if 1 <= index <= len(choices):
                    selected_indices.append(index)
                else:
                    print(f"Please enter a number between 1 and {len(choices)}.")
                    valid_input = False
                    break
            if valid_input:
                break
        return selected_indices



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
        for src in self.src_selected:
            self.logger.add_logger(f"sources/{self.modules['sources'][src - 1]}")
        for sink in self.sink_selected:
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

        source_label = QLabel(self)
        source_label.setText("Sources:")
        source_label.setGeometry(20, 10, 50, 10)

        #Create checkboxes for each source option
        sources = self.modules.get("sources")
        up_source = [source.capitalize() for source in sources]
        self.src_dict = {source: i + 1 for i, source in enumerate(up_source)}
        self.src_checkboxes = [QCheckBox(f"{src}") for src in up_source]
        self.src_selected = []
        
        # Layout for source checkboxes
        self.src_layout = QGridLayout()
        row = 0
        col = 0
        for checkbox in self.src_checkboxes:
            self.src_layout.addWidget(checkbox, row, col)
            col += 1
            if col == 3:  # Three checkboxes per row
                col = 0
                row += 1

        source_list = QWidget()
        source_list.setLayout(self.src_layout)
        source_list.setContentsMargins(0, 0, 0, 0)

        #Connect checkbox state to signals to detect which sources were selected 
        for checkbox in self.src_checkboxes:
            checkbox.stateChanged.connect(self.update_selected)

        #Create a sink label
        sink = QLabel(self)
        sink.setText("Sinks:")
        sink.setGeometry(20, 200, 50, 10)
        sink.setContentsMargins(0,0,0,0)

        #Create checkboxes for each sink option 
        sinks = self.modules.get("sinks")
        up_sink = [sink.capitalize() for sink in sinks]
        self.sink_dict = {sink: i + 1 for i, sink in enumerate(up_sink)}
        self.sink_checkboxes = [QCheckBox(f"{sink}") for sink in up_sink]
        
        self.sink_selected = []
        #Layout for sink checkboxes
        self.sink_layout=QGridLayout()
        row = 0
        col = 0
        for checkbox in self.sink_checkboxes:
            self.sink_layout.addWidget(checkbox, row, col)
            col += 1
            if col == 3:
                col = 0
                row += 1
        sink_list = QWidget()
        sink_list.setLayout(self.sink_layout)
        sink_list.setContentsMargins(0,0,0,0)
        
        #Connect checkbox state to signals to detect which sources were selected 
        for checkbox in self.sink_checkboxes:
            checkbox.stateChanged.connect(self.update_selected)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )
        self.button_box.accepted.connect(self.construct_commands)
        self.button_box.rejected.connect(self.close)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.addWidget(source_list)  # Add source checkboxes in grid layout
        main_layout.addWidget(sink_list)
        main_layout.addWidget(self.button_box)

        self.setLayout(main_layout)  # Set the main layout for the dialog

    def construct_commands(self):
        self.selected_ok = True
        self.omnibus = ["python", "-m", "omnibus"]
        self.commands.append(self.omnibus)

        
        if self.src_selected:
            for selection in self.src_selected:
                source = [python_executable, f"sources/{self.modules['sources'][int(selection)-1]}/main.py"]
                self.commands.append(source)
                
        if self.sink_selected:
            for selection in self.sink_selected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection)-1]}/main.py"]
                self.commands.append(sink)
        self.close()

    def update_selected(self, state):
        checkbox = self.sender()
        text = checkbox.text()
        
        if checkbox in self.src_checkboxes:
            selected_list = self.src_selected
            index = self.src_dict[text]
        else:
            selected_list = self.sink_selected
            index = self.sink_dict[text]
        if checkbox.isChecked():
            if index not in selected_list:
                selected_list.append(int(index))        
        else:
            selected_list.remove(int(index))
        
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

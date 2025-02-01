import os
import signal
import subprocess
import sys
import time
import argparse
import sys
import logging
import json
from functools import partial
from dataclasses import dataclass

from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt.QtWidgets import (
    QApplication, QDialog, QLabel, QDialogButtonBox, QVBoxLayout,
    QWidget, QCheckBox, QGridLayout, QLineEdit
)

from logtool import Logger

# Some specific commands are needed for Windows vs macOS/Linux
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP
    python_executable = "venv/Scripts/python"
else:
    python_executable = "python"

# Blank exception just for processes to throw


class Finished(Exception):
    pass

@dataclass
class CommandStruct:
    command: list[str]
    stdout: bool = False
    stderr: bool = False # stderr is not used in this version

# CLI Launcher
class Launcher():
    def __init__(self) -> None:
        super().__init__()
        self.commands: list[CommandStruct] = []
        self.processes = []
        self.load_last: bool = False

        # Parse folders for sources and sinks
        self.modules = {"sources": os.listdir('sources'), "sinks": os.listdir('sinks')}
        self.src_state = [[False,""] for _ in self.modules.get("sources")] # Selected, args
        self.sink_state = [[False, False] for _ in self.modules.get("sources")] # Selected, stdout flag

        # Remove dot files
        for module in self.modules.keys():
            for item in self.modules[module]:
                if item.startswith("."):
                    self.modules[module].remove(item)

    def load_config(self):
        print("Loading last selected sources and sinks...")
        if not os.path.exists("lastrun.json"):
            print("No last run file found. Please select sources and sinks.")
            self.load_last = False
            self.print_choices()
            return
        with open('lastrun.json', 'r') as fp:
            data = json.load(fp)
            self.src_state = data['Sources']
            self.sink_state = data['Sinks']
            fp.close()

    # Print list of sources and sinks
    def print_choices(self):
        for module in self.modules.keys():
            print(f"{module.capitalize()}:")
            for i, item in enumerate(self.modules[module]):
                print(f"\t{i+1}. {item.capitalize()}")

    # Enter inputs for CLI launcher
    def input(self):
        
        if not self.load_last:
            #Source selection
            src_selected  = self.validate_inputs(self.modules['sources'], "Source")

            self.construct_argus(src_selected) # Construct arguments for sources

            #Sink selection 
            sink_selected = self.validate_inputs(self.modules['sinks'], "Sink")
            
            for sink in sink_selected:
                self.sink_state[sink-1][0] = True
                self.sink_state[sink-1][1] = True # Default stdout flag is True in CLI mode

            self.save_selected_to_config()

        #Command construction
        # omnibus = [python_executable, "-m", "omnibus", False]
        omnibus = CommandStruct(command=[python_executable, "-m", "omnibus"], stdout=False)
        self.commands.append(omnibus)
        self.construct_commands_cli(self.src_state, self.sink_state)
        
    def construct_argus(self, src_list):
        for src in src_list:
            arg = input(f"Enter the arguments for the source {self.modules['sources'][src-1]} (default \"\"): ")
            self.src_state[src-1] = [True, arg]

    #Construct commands for the selection
    def construct_commands_cli(self, src_list, sink_list): # This is not support for stdout flag 
        for src in src_list:
            if src[0]:
                command = [python_executable, f"sources/{self.modules['sources'][self.src_state.index(src)]}/main.py"]
                if src[1] != "":
                    command.append(src[1])
                source = CommandStruct(command=command, stdout=False)
                self.commands.append(source)

        for snk in sink_list:
            if snk[0]:
                command = [python_executable, f"sinks/{self.modules['sinks'][self.sink_state.index(snk)]}/main.py"]
                sink = CommandStruct(command=command, stdout=snk[1])
                self.commands.append(sink)
        
        return self.commands

    #Validate the input selection for cli input
    def validate_inputs(self, choices, module):
        selected_indices=[]
        while True:
            user_input = input(f"\nPlease enter your {module} choices [1-{len(choices)}] separated by spaces: ")

            #Split the input string into individual values
            selection = user_input.split()

            #Validate the input 
            valid_input = True
            
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
                    selected_indices.clear()
                    break
            if valid_input:
                break
        return selected_indices

    # Execute commands as subprocesses
    def subprocess(self):
        print(f"Launching... Run commands: {self.commands}")
        for command in self.commands:
            launch_command = command.command
            stdout = subprocess.PIPE if command.stdout else None
            stderr = subprocess.PIPE if command.stderr else None
            if sys.platform == "win32":
                process = subprocess.Popen(launch_command, stdout=stdout, stderr=stderr,
                                            creationflags=CREATE_NEW_PROCESS_GROUP)
            else:
                process = subprocess.Popen(launch_command, stdout=stdout, stderr=stderr)
            time.sleep(0.8)
            self.processes.append(process)

        print("Done!")

    # Create loggers
    def logging(self):
        self.logger = Logger()
        for idx, (select, _) in enumerate(self.src_state):
            if select:
                src = self.modules['sources'][idx]
                if src == "fake_parsley":
                    self.logger.add_logger(f"sources/parsley")
                else:
                    self.logger.add_logger(f"sources/{src}")
        
        for idx, (select, _) in enumerate(self.sink_state):
            if select:
                sink = self.modules['sinks'][idx]
                self.logger.add_logger(f"sinks/{sink}")            
        
        print("Loggers Initiated")
    
    def save_selected_to_config(self):
        data = {}
        data ['Sources'] = self.src_state
        data ['Sinks'] = self.sink_state
        with open('lastrun.json', 'w+') as fp:
            json.dump(data, fp)

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


# GUI Launcher
class GUILauncher(Launcher, QDialog):
    def __init__(self):
        super().__init__()
        self.selected_ok = False

        self.setGeometry(300, 300, 500, 230)
        self.setFixedSize(700, 500)
        self.setWindowTitle("Omnibus Launcher")

        source_label = QLabel(self)
        source_label.setText("Sources:")
        source_label.setGeometry(20, 10, 50, 10)

        #Create checkboxes for each source option
        sources = self.modules.get("sources")
        self.sources = sources
        up_source = [source.capitalize() for source in sources]
        self.src_dict = {source: i + 1 for i, source in enumerate(up_source)}
        self.src_widgets = [(QCheckBox(f"{src}"), QLineEdit()) for src in up_source]
        for checkbox, args in self.src_widgets:
            args.setPlaceholderText("CLI args")
        self.src_state = [[False, ""] for _ in sources]

        
        #Layout for source checkboxes
        self.src_layout = QGridLayout()
        row = 0
        col = 0
        col_max = len(self.src_widgets) // 3 + 1 # Maximum 3 lines of checkboxes
        for checkbox, args in self.src_widgets:
            self.src_layout.addWidget(checkbox, row, col)
            self.src_layout.addWidget(args, row + 1, col)
            col += 1
            if col == col_max: 
                col = 0
                row += 2

        source_list = QWidget()
        source_list.setLayout(self.src_layout)
        source_list.setContentsMargins(0, 0, 0, 0)


        #Connect checkbox state to signals to detect which sources were selected 
        for i, (checkbox, args) in enumerate(self.src_widgets):
            # https://docs.python.org/3/faq/programming.html#why-do-lambdas-defined-in-a-loop-with-different-values-all-return-the-same-result
            def stateChanged(state, index):
                self.src_state[index][0] = state == 2
            def textChanged(text, index):
                self.src_state[index][1] = text
            checkbox.stateChanged.connect(partial(stateChanged,index = i))
            args.textChanged.connect(partial(textChanged,index = i))

        #Create a sink label
        sink = QLabel(self)
        sink.setText("Sinks:")
        sink.setGeometry(20, 230, 50, 10)
        sink.setContentsMargins(0,0,0,0)

        #Create checkboxes for each sink option 
        sinks = self.modules.get("sinks")
        up_sink = [sink.capitalize() for sink in sinks]
        self.sink_dict = {sink: i + 1 for i, sink in enumerate(up_sink)}
        self.sinks_widgets = [(QCheckBox(f"{sink}"), QCheckBox(f"stdout?")) for sink in up_sink]
        
        #Layout for sink checkboxes
        self.sink_layout=QGridLayout()
        row = 0
        col = 0
        for checkbox, std_out in self.sinks_widgets:
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            group_layout.addWidget(checkbox)
            group_layout.addWidget(std_out)
            group_widget.setLayout(group_layout)
            group_widget.setStyleSheet("border: 1px solid black; padding: 5px;")
            self.sink_layout.addWidget(group_widget, row, col)
            col += 1
            if col == 5:  # Three groups per row
                col = 0
                row += 1
        sink_list = QWidget()
        sink_list.setLayout(self.sink_layout)
        sink_list.setContentsMargins(0, 0, 0, 0)
        
        #Connect checkbox state to signals to detect which sink were selected 
        for i, (checkbox, std_out) in enumerate(self.sinks_widgets):
            def stateChanged(state, index):
                self.sink_state[index][0] = state == 2
            def stdOutChanged(state, index):
                self.sinks_widgets[index][0].setChecked(True if state == 2 else False)
                self.sinks_widgets[index][0].setEnabled(False if state == 2 else True)
                self.sink_state[index][1] = True if state == 2 else False
            checkbox.stateChanged.connect(partial(stateChanged,index = i))
            std_out.stateChanged.connect(partial(stdOutChanged,index = i))

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok
        )

        self.button_box.accepted.connect(self.construct_commands)
        self.button_box.rejected.connect(self.close)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.addWidget(source_list) 
        main_layout.addWidget(sink_list)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def construct_commands(self):
        self.selected_ok = True
        omnibus = CommandStruct(command=[python_executable, "-m", "omnibus"], stdout=False) # False is for stdout flag
        self.commands.append(omnibus)

        for src in self.src_state:
            if src[0]:
                command = [python_executable, f"sources/{self.modules['sources'][self.src_state.index(src)]}/main.py"]
                if src[1] != "":
                    command.append(src[1])
                source = CommandStruct(command=command, stdout=False)
                self.commands.append(source)

        for snk in self.sink_state:
            if snk[0]:
                command = [python_executable, f"sinks/{self.modules['sinks'][self.sink_state.index(snk)]}/main.py"]
                if snk[1]: # Check stdout flag
                    sink = CommandStruct(command=command, stdout=True)
                else:
                    sink = CommandStruct(command=command, stdout=False)
                self.commands.append(sink)
        self.close()

    def closeEvent(self, event):
        if self.selected_ok:
            self.save_selected_to_config()
            event.accept()
        else:
            sys.exit()


def main():
    parser = argparse.ArgumentParser(description='Omnibus Launcher')
    parser.add_argument('--text', action='store_true', help='Use text input mode')
    parser.add_argument('--last', action='store_true', help='Use last selected sources and sinks')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    if args.last or args.text:
    # If 'python launcher.py --last' is run this block of code will execute
        launcher = Launcher()
        if args.last:
            print("Running with last selected sources and sinks")
            launcher.load_last = True
            launcher.load_config()
        # If 'python launcher.py --text' is run this block of code will execute
        elif args.text:
            print("Running in text mode")
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

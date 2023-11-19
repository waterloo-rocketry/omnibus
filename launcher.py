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
        # Parse folders for sources and sinks
        self.modules = {"sources" : os.listdir('sources'), "sinks" : os.listdir('sinks')}

    # Enter inputs for CLI launcher
    def input(self):
        # Remove dot files
        for module in self.modules.keys():
            for item in self.modules[module]:
                if item.startswith("."):
                    self.modules[module].remove(item)

        for module in self.modules.keys():
            print(f"{module.capitalize()}:")
            for i, item in enumerate(self.modules[module]):
                print(f"\t{i+1}. {item.capitalize()}")

        # Construct CLI commands to start Omnibus
        self.source_selection = input(f"\nPlease enter your Source choice [1-{len(self.modules['sources'])}]: ")
        self.sink_selection = input(f"Please enter your Sink choice [1-{len(self.modules['sinks'])}]: ")
        self.omnibus = [python_executable, "-m", "omnibus"]
        self.source = [python_executable, f"sources/{self.modules['sources'][int(self.source_selection) - 1]}/main.py"]
        self.sink = [python_executable, f"sinks/{self.modules['sinks'][int(self.sink_selection) - 1]}/main.py"]

        self.commands = [self.omnibus, self.source, self.sink]

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
        self.logger.add_logger(f"sources/{self.modules['sources'][int(self.source_selection) - 1]}")
        self.logger.add_logger(f"sinks/{self.modules['sinks'][int(self.sink_selection) - 1]}")
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
                # self.logger.log_output(process, output)
                print(output)

                # Log errors
                if err and "KeyboardInterrupt" not in err:
                #     self.logger.log_error(process, err)
                    print(err)
                    
            # logging.shutdown()
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
        self.commands = []

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
        source.setGeometry(20, 50, 150, 20)

        # Create a dropdown for source
        self.source_dropdown = QComboBox(self)
        self.source_dropdown.setGeometry(90, 52, 150, 20)

        # Add items to the sources dropdown
        for source in self.modules.get("sources"):
            self.source_dropdown.addItem(source)

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sink:")
        sink.setGeometry(20, 90, 150, 20)

        # Create a dropdown for sink
        self.sink_dropdown = QComboBox(self)
        self.sink_dropdown.setGeometry(90, 92, 150, 20)

        # Add items to the sinks dropdown
        for sink in self.modules.get("sinks"):
            self.sink_dropdown.addItem(sink)

        # Enter selections button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.launching_gui)

        # Add button to layout
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
    
    def launching_gui(self):
        # Selected source and sink in GUI
        self.selected_source = self.source_dropdown.currentText()
        self.selected_sink = self.sink_dropdown.currentText()

        self.omnibus = ["python", "-m", "omnibus"]
        self.source = ["python", f"sources/{self.selected_source}/main.py"]
        self.sink = ["python", f"sinks/{self.selected_sink}/main.py"]

        self.commands = [self.omnibus, self.source, self.sink]

        self.close()


def main():
    parser = argparse.ArgumentParser(description='Omnibus Launcher')
    parser.add_argument('--text', action='store_true', help='Use text input mode')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    # If 'python launcher.py --text' is run this block of code will execute
    if args.text:
        print("Running in text mode")
        launcher = Launcher()
        launcher.input()
        launcher.subprocess()
        launcher.logging()
        launcher.terminate()

    # If 'python launcher.py' is run this this block of code will execute
    else:
        print("Running in GUI mode")
        gui_launcher = GUILauncher()
        gui_launcher.show()
        gui_launcher.logging()
        app.exec()
        gui_launcher.subprocess()
        gui_launcher.terminate()

if __name__ == '__main__':
    main()

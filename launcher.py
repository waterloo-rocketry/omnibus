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

# Parse folders for sources and sinks
modules = {"sources" : os.listdir('sources'), "sinks" : os.listdir('sinks')}

# Blank exception just for processes to throw
class Finished(Exception):
    pass

# CLI Launcher
class Launcher(QDialog):
    def __init__(self):
        super().__init__()

        # Remove dot files
        for module in modules.keys():
            for item in modules[module]:
                if item.startswith("."):
                    modules[module].remove(item)

        for module in modules.keys():
            print(f"{module.capitalize()}:")
            for i, item in enumerate(modules[module]):
                print(f"\t{i+1}. {item.capitalize()}")

        # Construct CLI commands to start Omnibus
        source_selection = input(f"\nPlease enter your Source choice [1-{len(modules['sources'])}]: ")
        sink_selection = input(f"Please enter your Sink choice [1-{len(modules['sinks'])}]: ")
        omnibus = [python_executable, "-m", "omnibus"]
        source = [python_executable, f"sources/{modules['sources'][int(source_selection) - 1]}/main.py"]
        sink = [python_executable, f"sinks/{modules['sinks'][int(sink_selection) - 1]}/main.py"]

        # Create loggers
        logger = Logger()
        logger.add_logger(f"sources/{modules['sources'][int(source_selection) - 1]}")
        logger.add_logger(f"sinks/{modules['sinks'][int(sink_selection) - 1]}")
        print("Loggers Initiated")

        commands = [omnibus, source, sink]
        processes = []
        print("Launching... ", end="")

        # Execute commands as subprocesses
        for command in commands:
            if sys.platform == "win32":
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                        creationflags=CREATE_NEW_PROCESS_GROUP)
                time.sleep(0.5)
            else:
                process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                time.sleep(0.5)
            processes.append(process)

        print("Done!")

    # If any file exits or the user presses control + c,
    # terminate all other files that are running
    def terminate(self):
        try:
            while True:
                for process in processes:
                    if process.poll() != None:
                        raise Finished
        except (Finished, KeyboardInterrupt, Exception):
            for process in processes:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    process.send_signal(signal.SIGINT)

                # Dump output and error (if exists) from every
                # process to the coresponding log file
                output, err = process.communicate()
                output, err = output.decode(), err.decode()
                
                # Log outputs
                logger.log_output(process, output)

                # Log errors
                if err and "KeyboardInterrupt" not in err:
                    logger.log_error(process, err)
                    
            logging.shutdown()
        finally:
            for process in processes:
                if sys.platform == "win32":
                    os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                else:
                    process.send_signal(signal.SIGINT)        

# GUI Launcher
class GUILauncher(Launcher, QDialog):
    def __init__(self):
        super().__init__()

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
        for source in modules.get("sources"):
            self.source_dropdown.addItem(source)

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sink:")
        sink.setGeometry(20, 90, 150, 20)

        # Create a dropdown for sink
        self.sink_dropdown = QComboBox(self)
        self.sink_dropdown.setGeometry(90, 92, 150, 20)

        # Add items to the sinks dropdown
        for sink in modules.get("sinks"):
            self.sink_dropdown.addItem(sink)

        # Enter selections button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.enter_selections)

        # Add button to layout
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
    
    def enter_selections(self):
        # Selected source and sink in GUI
        selected_source = self.source_dropdown.currentText()
        selected_sink = self.sink_dropdown.currentText()

        omnibus = ["python", "-m", "omnibus"]
        source = ["python", f"sources/{selected_source}/main.py"]
        sink = ["python", f"sinks/{selected_sink}/main.py"]
        commands = [omnibus, source, sink]
        processes = []
        print("Launching... ", end="")

        # Close the window
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
        launcher.terminate()

    # If 'python launcher.py' is run this this block of code will execute
    else:
        print("Running in GUI mode")
        gui_launcher = GUILauncher()
        gui_launcher.show()
        sys.exit(app.exec())

if __name__ == '__main__':
    main()

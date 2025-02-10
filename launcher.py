#!/usr/bin/env python3
import os
import signal
import subprocess
import sys
import time
import argparse
import logging
import json
from functools import partial
from dataclasses import dataclass
from typing import List, Tuple

# Import from Qt – note: these come from pyqtgraph’s wrapper
from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt import QtCore
from pyqtgraph.Qt.QtWidgets import (
    QApplication, QDialog, QLabel, QDialogButtonBox, QVBoxLayout,
    QWidget, QCheckBox, QGridLayout, QLineEdit
)


from logtool import Logger

# Select proper Python executable depending on platform
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP
    python_executable = os.path.join("venv", "Scripts", "python")
else:
    python_executable = "python"


class Finished(Exception):
    """Custom exception to indicate one or more processes have finished."""
    pass


@dataclass
class CommandStruct:
    command: List[str]
    stdout: bool = False
    stderr: bool = False  # stderr is not used in this version


class Launcher:
    """
    Base launcher class that supports CLI-based input of sources and sinks,
    process launching, logging, and graceful termination.
    """
    def __init__(self) -> None:
        self.commands: List[CommandStruct] = []
        self.processes: List[subprocess.Popen] = []
        self.load_last: bool = False

        # Read available modules for sources and sinks.
        self.modules = {
            "sources": [item for item in os.listdir('sources') if not item.startswith('.')],
            "sinks":   [item for item in os.listdir('sinks') if not item.startswith('.')]
        }
        # Each source: [selected_flag, args]
        self.src_state: List[Tuple[bool, str]] = [(False, "") for _ in self.modules["sources"]]
        # Each sink: [selected_flag, stdout_flag]
        self.sink_state: List[Tuple[bool, bool]] = [(False, False) for _ in self.modules["sinks"]]

    def load_config(self) -> None:
        """Load the configuration from 'lastrun.json' if it exists."""
        print("Loading last selected sources and sinks...")
        if not os.path.exists("lastrun.json"):
            print("No last run file found. Please select sources and sinks.")
            self.load_last = False
            self.print_choices()
            return

        try:
            with open('lastrun.json', 'r') as fp:
                data = json.load(fp)
                self.src_state = data.get('Sources', self.src_state)
                self.sink_state = data.get('Sinks', self.sink_state)
        except Exception as e:
            print(f"Error reading configuration: {e}")
            self.load_last = False

    def print_choices(self) -> None:
        """Print out available source and sink modules."""
        for module, items in self.modules.items():
            print(f"{module.capitalize()}:")
            for i, item in enumerate(items, start=1):
                print(f"\t{i}. {item.capitalize()}")

    def input(self) -> None:
        """
        CLI input for selecting sources and sinks. Prompts the user and
        updates the internal state accordingly.
        """
        if not self.load_last:
            # Source selection
            src_indices = self.validate_inputs(self.modules["sources"], "Source")
            self.construct_args(src_indices)

            # Sink selection
            sink_indices = self.validate_inputs(self.modules["sinks"], "Sink")
            for idx in sink_indices:
                # Adjust index (input is 1-indexed)
                self.sink_state[idx - 1] = (True, True)  # default stdout flag True in CLI mode

            self.save_selected_to_config()

        # Add the omnibus command
        omnibus = CommandStruct(command=[python_executable, "-m", "omnibus"], stdout=False)
        self.commands.append(omnibus)
        self.construct_commands_cli()

    def construct_args(self, selected_indices: List[int]) -> None:
        """For each selected source, prompt the user for additional arguments."""
        for idx in selected_indices:
            # Convert from 1-indexed to 0-indexed
            args_input = input(f"Enter the arguments for the source {self.modules['sources'][idx - 1]} (default \"\"): ")
            self.src_state[idx - 1] = (True, args_input.strip())

    def construct_commands_cli(self) -> List[CommandStruct]:
        """
        Build the list of commands to launch based on selected sources and sinks.
        Returns the list of CommandStruct instances.
        """
        # Build commands for sources
        for i, (selected, args) in enumerate(self.src_state):
            if selected:
                command = [python_executable, os.path.join("sources", self.modules["sources"][i], "main.py")]
                if args:
                    command.append(args)
                self.commands.append(CommandStruct(command=command, stdout=False))
        # Build commands for sinks
        for i, (selected, stdout_flag) in enumerate(self.sink_state):
            if selected:
                command = [python_executable, os.path.join("sinks", self.modules["sinks"][i], "main.py")]
                self.commands.append(CommandStruct(command=command, stdout=stdout_flag))
        return self.commands

    def validate_inputs(self, choices: List[str], module: str) -> List[int]:
        """
        Validate the user’s input for source or sink selection.
        Returns a list of selected (1-indexed) indices.
        """
        selected_indices = []
        while True:
            user_input = input(f"\nPlease enter your {module} choices [1-{len(choices)}] separated by spaces: ")
            parts = user_input.split()
            valid = True
            temp_indices = []
            for part in parts:
                if not part.isdigit():
                    print(f"Invalid input: '{part}' is not a number.")
                    valid = False
                    break
                idx = int(part)
                if 1 <= idx <= len(choices):
                    temp_indices.append(idx)
                else:
                    print(f"Please enter a number between 1 and {len(choices)}.")
                    valid = False
                    break
            if valid:
                selected_indices = temp_indices
                break
        return selected_indices

    def launch_processes(self) -> None:
        """Launch all configured commands as subprocesses."""
        print(f"Launching processes with the following commands:")
        for cmd_struct in self.commands:
            print(" ", " ".join(cmd_struct.command))
            try:
                stdout = subprocess.PIPE if cmd_struct.stdout else None
                stderr = subprocess.PIPE if cmd_struct.stderr else None
                if sys.platform == "win32":
                    process = subprocess.Popen(
                        cmd_struct.command,
                        stdout=stdout,
                        stderr=stderr,
                        creationflags=CREATE_NEW_PROCESS_GROUP
                    )
                else:
                    process = subprocess.Popen(
                        cmd_struct.command,
                        stdout=stdout,
                        stderr=stderr
                    )
                time.sleep(2)  # slight delay to allow process startup
                self.processes.append(process)
            except Exception as e:
                print(f"Error launching process: {e}")
            time.sleep(2)  # slight delay to allow process startup
            self.processes.append(process)
        print("All processes launched!")

    def setup_loggers(self) -> None:
        """Initialize the logger for each selected module."""
        self.logger = Logger()
        # Add logger for selected sources
        for i, (selected, _) in enumerate(self.src_state):
            if selected:
                src = self.modules["sources"][i]
                # Use a different name if needed
                module_name = f"sources/{src}" if src != "fake_parsley" else "sources/parsley"
                self.logger.add_logger(module_name)

        # Add logger for selected sinks
        for i, (selected, _) in enumerate(self.sink_state):
            if selected:
                sink = self.modules["sinks"][i]
                self.logger.add_logger(f"sinks/{sink}")

        print("Loggers initiated.")

    def save_selected_to_config(self) -> None:
        """Save the current source and sink selections to 'lastrun.json'."""
        data = {
            'Sources': self.src_state,
            'Sinks': self.sink_state
        }
        try:
            with open('lastrun.json', 'w') as fp:
                json.dump(data, fp)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def terminate(self) -> None:
        """
        Monitor all subprocesses, and on termination (either via finish or KeyboardInterrupt),
        send termination signals and log output.
        """
        try:
            # Poll processes until one finishes or user interrupts
            while True:
                for process in self.processes:
                    all_finished = all(process.poll() is not None for process in self.processes)
                    if all_finished:
                        raise Finished
        except (Finished, KeyboardInterrupt, Exception):
            for process in self.processes:
                try:
                    if sys.platform == "win32":
                        os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                    else:
                        process.send_signal(signal.SIGINT)
                    output, err = process.communicate(timeout=5)
                    # Decode outputs if available
                    out_str = output.decode() if output else ""
                    err_str = err.decode() if err else ""
                    self.logger.log_output(process, out_str)
                    if err_str and "KeyboardInterrupt" not in err_str:
                        self.logger.log_error(process, err_str)
                except Exception as e:
                    print(f"Error terminating process {process.pid}: {e}")
            logging.shutdown()
        finally:
            for process in self.processes:
                try:
                    if sys.platform == "win32":
                        os.kill(process.pid, signal.CTRL_BREAK_EVENT)
                    else:
                        process.send_signal(signal.SIGINT)
                except Exception:
                    pass


class GUILauncher(Launcher, QDialog):
    """
    GUI-based launcher using PyQt. Inherits from Launcher to reuse command
    construction and process management methods.
    """
    def __init__(self):
        # Initialize both parent classes explicitly
        Launcher.__init__(self)
        QDialog.__init__(self)
        self.selected_ok = False
        self.setWindowTitle("Omnibus Launcher")
        self.setFixedSize(700, 600)

        # Checkbox for if start with the omnibus server
        self.omnibus_checkbox = QCheckBox("Advanced: Start local Omnibus server? (Do NOT use when the DAQ box is also online)")
        self.omnibus_checkbox.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.omnibus_checkbox.setChecked(False)
        self.omnibus_checkbox.stateChanged.connect(self.on_omnibus_state_changed)
        
        self.on_omnibus_state_changed(2)  # default to checked
        

        # Setup sources UI
        source_label = QLabel("Sources:")
        self.sources = self.modules["sources"]
        self.src_state = [(False, "") for _ in self.sources]  # reset state

        # Create checkboxes and line edits for each source
        self.src_widgets: List[Tuple[QCheckBox, QLineEdit]] = []
        for src in self.sources:
            checkbox = QCheckBox(src.capitalize())
            line_edit = QLineEdit()
            line_edit.setPlaceholderText("CLI args")
            self.src_widgets.append((checkbox, line_edit))

        # Arrange source widgets in a grid layout
        self.src_layout = QGridLayout()
        col_max = max(1, len(self.src_widgets) // 3 + 1)
        row = 0
        col = 0
        for i, (checkbox, args) in enumerate(self.src_widgets):
            self.src_layout.addWidget(checkbox, row, col)
            self.src_layout.addWidget(args, row + 1, col)
            col += 1
            if col >= col_max:
                col = 0
                row += 2
        source_list_widget = QWidget()
        source_list_widget.setLayout(self.src_layout)

        # Connect signals for source widgets
        for i, (checkbox, args) in enumerate(self.src_widgets):
            checkbox.stateChanged.connect(partial(self.on_source_state_changed, index=i))
            args.textChanged.connect(partial(self.on_source_text_changed, index=i))

        # Setup sinks UI
        sink_label = QLabel("Sinks:")
        self.sinks = self.modules["sinks"]
        self.sink_state = [(False, False) for _ in self.sinks]  # reset state

        # Create checkboxes for sink selection and an optional stdout flag
        self.sink_widgets: List[Tuple[QCheckBox, QCheckBox]] = []
        self.sink_layout = QGridLayout()
        for i, sink in enumerate(self.sinks):
            sink_checkbox = QCheckBox(sink.capitalize())
            stdout_checkbox = QCheckBox("stdout?")
            sink_checkbox.setStyleSheet("border: none;")
            stdout_checkbox.setStyleSheet("border: none;")
            self.sink_widgets.append((sink_checkbox, stdout_checkbox))
            group_widget = QWidget()
            group_layout = QVBoxLayout()
            group_layout.addWidget(sink_checkbox)
            group_layout.addWidget(stdout_checkbox)
            group_widget.setLayout(group_layout)
            group_widget.setStyleSheet("border: 1px solid black; padding: 5px;")
            row = i // 5
            col = i % 5
            self.sink_layout.addWidget(group_widget, row, col)

            # Connect signals for sink widgets
            sink_checkbox.stateChanged.connect(partial(self.on_sink_state_changed, index=i))
            stdout_checkbox.stateChanged.connect(partial(self.on_stdout_state_changed, index=i))

        sink_list_widget = QWidget()
        sink_list_widget.setLayout(self.sink_layout)

        # Dialog button box
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.button_box.accepted.connect(self.construct_commands)
        self.button_box.rejected.connect(self.close)

        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(source_label)
        main_layout.addWidget(source_list_widget)
        main_layout.addWidget(sink_label)
        main_layout.addWidget(sink_list_widget)
        main_layout.addWidget(self.omnibus_checkbox)
        main_layout.addWidget(self.button_box)
        self.setLayout(main_layout)

    def on_source_state_changed(self, state: int, index: int) -> None:
        """Handle source checkbox state changes."""
        self.src_state[index] = (state == 2, self.src_state[index][1])

    def on_source_text_changed(self, text: str, index: int) -> None:
        """Handle changes in source argument text fields."""
        self.src_state[index] = (self.src_state[index][0], text.strip())

    def on_sink_state_changed(self, state: int, index: int) -> None:
        """Handle sink checkbox state changes."""
        self.sink_state[index] = (state == 2, self.sink_state[index][1])

    def on_stdout_state_changed(self, state: int, index: int) -> None:
        """
        When the stdout checkbox is toggled, force the sink checkbox to be selected
        and disable it if stdout is enabled.
        """
        sink_checkbox, stdout_checkbox = self.sink_widgets[index]
        if state == 2:
            sink_checkbox.setChecked(True)
            sink_checkbox.setEnabled(False)
            self.sink_state[index] = (True, True)
        else:
            sink_checkbox.setEnabled(True)
            # If unchecked, preserve the selection state for stdout flag
            self.sink_state[index] = (sink_checkbox.isChecked(), False)
            
    def on_omnibus_state_changed(self, state: int) -> None:
        """Handle omnibus checkbox state changes."""
        omnibus = CommandStruct(command=[python_executable, "-m", "omnibus"], stdout=False)
        if state == 2:
            self.commands = [omnibus]
        else:
            self.commands = []

    def construct_commands(self) -> None:
        """Construct commands from the GUI selections and close the dialog."""
        self.selected_ok = True
        # Add omnibus command

        for idx, src in enumerate(self.src_state):
            if src[0]:
                command = [python_executable, f"sources/{self.modules['sources'][idx]}/main.py"]
                if src[1] != "":
                    command.append(src[1])
                source = CommandStruct(command=command, stdout=False)
                self.commands.append(source)

        for idx, snk in enumerate(self.sink_state):
            if snk[0]:
                command = [python_executable, f"sinks/{self.modules['sinks'][idx]}/main.py"]
                if snk[1]: # Check stdout flag
                    sink = CommandStruct(command=command, stdout=True)
                else:
                    sink = CommandStruct(command=command, stdout=False)
                self.commands.append(sink)
        self.close()

    def closeEvent(self, event) -> None:
        """Override the close event. Exit if not accepted."""
        if self.selected_ok:
            event.accept()
        else:
            print("No sources or sinks selected. Exiting...")
            sys.exit(0)

    def keyPressEvent(self, event) -> None:
        """Handle key press events. Exit if 'q' or 'Esc' is pressed."""
        if event.key() in (QtGui.QKeySequence.Quit, QtCore.Qt.Key_Escape):
            self.close()
        else:
            super().keyPressEvent(event)


def main():
    parser = argparse.ArgumentParser(description='Omnibus Launcher')
    parser.add_argument('--text', action='store_true', help='Use text input mode')
    parser.add_argument('--last', action='store_true', help='Use last selected sources and sinks')
    args = parser.parse_args()

    app = QApplication(sys.argv)

    if args.last or args.text:
        launcher = Launcher()
        if args.last:
            print("Running with last selected sources and sinks")
            launcher.load_last = True
            launcher.load_config()
        elif args.text:
            print("Running in text mode")
            launcher.print_choices()

        launcher.input()
        launcher.launch_processes()
        launcher.setup_loggers()
        launcher.terminate()
    else:
        print("Running in GUI mode")
        gui_launcher = GUILauncher()
        gui_launcher.show()
        app.exec()
        gui_launcher.launch_processes()
        gui_launcher.setup_loggers()
        gui_launcher.terminate()


if __name__ == '__main__':
    main()

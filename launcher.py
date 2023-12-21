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
from PySide6.QtGui import QStandardItemModel
from PySide6.QtCore import Qt

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



# GUI Launcher
class GUILauncher(Launcher, QDialog):
    def __init__(self):
        super().__init__()
        self.selected_ok = False

        # Sets window title and ensures size of dialog is fixed
        self.setGeometry(300, 300, 500, 230)
        self.setFixedSize(500, 230)
        #self.setMinimumWidth(500)
        #self.setMinimumHeight(600)
        self.setWindowTitle("Omnibus Launcher")

        # Description / Title
        description = QLabel(self)
        description.setText("Please enter your source and sink choices")
        description.setGeometry(20, 5, 500, 50)
        description.setFont(QtGui.QFont("", 18))

        # Create a source label
        source = QLabel(self)
        source.setText("Source:")
        source.setGeometry(20, 53, 150, 20)

        # Create a dropdown for source (old)
            #self.source_dropdown = QComboBox(self)
            #self.source_dropdown.setGeometry(90, 52, 150, 30)

        # Add items to the sources dropdown
            #for source in self.modules.get("sources"):
                #self.source_dropdown.addItem(source)

        #updated checkable combo box for source
        self.srcList=QComboBox(self)
        self.srcList.setModel(QStandardItemModel(self.srcList))
        self.srcList.setEditable(True)
        self.srcList.setMaxVisibleItems(5)
        self.srcList.setGeometry(90, 52, 150, 30)
        self.srcList.view().pressed.connect(lambda index: self.selected_item(index, "srcList"))
        

        #populate the selection list 
        for src in self.modules.get("sources"):
            self.srcList.addItem(src)  

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sink:")
        sink.setGeometry(20, 93, 150, 20)

        # Create a dropdown for sink (old)
            #self.sink_dropdown = QComboBox(self)
            #self.sink_dropdown.setGeometry(90, 92, 150, 30)

        # Add items to the sinks dropdown
            #for sink in self.modules.get("sinks"):
                #self.sink_dropdown.addItem(sink)

        #updated checkable combo box for sink
        self.sinkList=QComboBox(self)
        self.sinkList.setModel(QStandardItemModel(self.sinkList))
        self.sinkList.setEditable(True)
        self.sinkList.setMaxVisibleItems(5)
        self.sinkList.setGeometry(90, 92, 150, 30)
        self.sinkList.view().pressed.connect(lambda index: self.selected_item(index, "sinkList"))
        

        #populate the selection list 
        for sink in self.modules.get("sinks"):
            self.sinkList.addItem(sink)  

        # Enter selections button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.construct_commands) #modify the chain of actions from here 
        self.button_box.rejected.connect(self.close)

        # Add button to layout
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)

    def selected_item(self, index, model_name):
        #get the item that is selected 
        
        if model_name=="srcList":
            model=self.srcList.model()
        elif model_name=="sinkList":
            model=self.sinkList.model()
        
        item=model.itemFromIndex(index)

        #verify if the item is in a checked state 
        if item.checkState() == Qt.Checked:
            item.setCheckState(Qt.Unchecked)
        else:
            item.setCheckState(Qt.Checked)
        
        #self.check_items()

    def check_items(self, model):
        #this function may not be needed 
        checkedItems=[] #return this list only when the done is clicked 
        indexList=[]
        #traverse items that are checked 
        for row in range(model.rowCount()):
            item = model.item(row)
            if item.checkState() == Qt.Checked:
                checkedItems.append(item.text())
                index=model.indexFromItem(item).row()
                indexList.append(index)
        #print("Index list: ",indexList)
        return indexList


    def construct_commands(self):
        self.selected_ok = True

        # Get selected source and sink in GUI
        self.srcSelected=self.check_items(self.srcList.model())
        #print (self.srcSelected)

        self.sinkSelected=self.check_items(self.sinkList.model())
        #print(self.sinkSelected)
        
        self.omnibus = ["python", "-m", "omnibus"]
        self.commands.append(self.omnibus)

        
        #old
        #self.source_selection = self.modules['sources'].index(self.source_dropdown.currentText())
        #self.sink_selection = self.modules['sinks'].index(self.sink_dropdown.currentText())

        
        if self.srcSelected:
            for selection in self.srcSelected:
                #print("current selection: ", selection)
                source=[python_executable, f"sources/{self.modules['sources'][int(selection) - 1]}/main.py"]
                #source = ["python", f"sources/{selection}/main.py"]
                self.commands.append(source)
                
        if self.sinkSelected:
            for selection in self.sinkSelected:
                sink = [python_executable, f"sinks/{self.modules['sinks'][int(selection) - 1]}/main.py"]
                #sink = ["python", f"sinks/{selection}/main.py"]
                self.commands.append(sink)
                
                
        
        #self.source = ["python", f"sources/{self.source_dropdown.currentText()}/main.py"]
        #self.sink = ["python", f"sinks/{self.sink_dropdown.currentText()}/main.py"]

        #self.commands = [self.omnibus, self.source, self.sink]
        #print(self.commands)
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

cosmetic issues:
-the window is not resizeable, the words in the label are truncated 
(resize the window)

'''
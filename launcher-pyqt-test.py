from pyqtgraph.Qt import QtGui
from pyqtgraph.Qt.QtWidgets import QApplication, QDialog, QLabel, QComboBox, QDialogButtonBox, QVBoxLayout

import sys

class Launcher(QDialog):
    def __init__(self):
        super().__init__()

        self.setGeometry(300, 300, 400, 220)
        self.setWindowTitle("Omnibus Launcher")

        # Description / Title
        description = QLabel(self)
        description.setText("Please enter your source and sink choices")
        description.setGeometry(20, 10, 400, 20)
        description.setFont(QtGui.QFont("", 18))

        # Create a source label
        source = QLabel(self)
        source.setText("Source:")
        source.setGeometry(20, 50, 150, 20)

        # Create a dropdown for source
        self.source_dropdown = QComboBox(self)
        self.source_dropdown.setGeometry(90, 52, 150, 20)

        # Add items to the sources dropdown
        self.source_dropdown.addItem("Ni")
        self.source_dropdown.addItem("Replay_log")
        self.source_dropdown.addItem("Pipe_output")
        self.source_dropdown.addItem("Parsley")
        self.source_dropdown.addItem("Rlcs")
        self.source_dropdown.addItem("Fakeni")
        self.source_dropdown.addItem("Fake_parsley")
        self.source_dropdown.addItem("Payload_fake")

        # Create a sink label
        sink = QLabel(self)
        sink.setText("Sink:")
        sink.setGeometry(20, 90, 150, 20)

        # Create a dropdown for sink
        self.sink_dropdown = QComboBox(self)
        self.sink_dropdown.setGeometry(90, 92, 150, 20)

        # Add items to the sources dropdown
        self.sink_dropdown.addItem("Txtconsole")
        self.sink_dropdown.addItem("Printer")
        self.sink_dropdown.addItem("Dashboard")
        self.sink_dropdown.addItem("Gpsd")
        self.sink_dropdown.addItem("Globallog")

        # Enter selections button
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        self.button_box.accepted.connect(self.enter_selections)

        # Add button to layout
        self.layout = QVBoxLayout()
        self.layout.addStretch(1)
        self.layout.addWidget(self.button_box)
        self.setLayout(self.layout)
    
    def enter_selections(self):
        selected_source = self.source_dropdown.currentText()
        selected_sink = self.sink_dropdown.currentText()

        # Do something with the selected values (e.g., save to a file, process, etc.)
        print("Selected Source:", selected_source)
        print("Selected Sink:", selected_sink)

        # Close the window
        self.close()

def main():
    app = QApplication(sys.argv)
    window = Launcher()
    window.show()
    sys.exit(app.exec())

main()

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QCheckBox, QPushButton

class CheckBoxDialog(QDialog):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Check Box Dialog")
        self.layout = QVBoxLayout()

        self.options = ["Option 1", "Option 2", "Option 3", "Option 4"]

        # Create checkboxes for each option
        self.checkboxes = [QCheckBox(option) for option in self.options]

        # Add checkboxes to the layout
        for checkbox in self.checkboxes:
            self.layout.addWidget(checkbox)

        # Button to collect checked options
        self.collect_button = QPushButton("Collect Checked Options")
        self.collect_button.clicked.connect(self.collect_checked_options)
        self.layout.addWidget(self.collect_button)

        self.setLayout(self.layout)

    def collect_checked_options(self):
        checked_options = [checkbox.text() for checkbox in self.checkboxes if checkbox.isChecked()]
        print("Checked options:", checked_options)


def main():
    app = QApplication(sys.argv)
    dialog = CheckBoxDialog()
    dialog.exec_()


if __name__ == '__main__':
    main()

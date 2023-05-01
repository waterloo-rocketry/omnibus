from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtCore import Qt


class ConfirmDialog(QtWidgets.QDialog):
    def __init__(self, property_name, description, parent=None):
        super().__init__(parent)

        self.setWindowTitle(property_name)

        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)

        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel(description)
        self.layout.addWidget(message)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

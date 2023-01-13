from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtCore import Qt


class CheckBoxDialog(QtWidgets.QDialog):
    def __init__(self, property_name, description, items, parent=None):
        super().__init__(parent)

        self.setWindowTitle(property_name)

        QBtn = QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel(description)
        self.layout.addWidget(message)
        # set up series checkboxes
        self.items = []
        for item in items:
            checkbox = QtWidgets.QCheckBox(item)
            self.items.append(checkbox)
            self.layout.addWidget(checkbox)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


def prompt_user(widget, property_name, description, prompt_type, items=None, can_add_items=False, okText="OK", cancelText="Cancel"):
    """
    Opens a pop up asking user for input.
    Returns None if input selection is not valid or user cancels
    """
    if prompt_type == "checkbox":
        # set up a checkbox dialog
        dia = CheckBoxDialog(property_name, description, items, widget)
        items_length = len(items)
        # retrieve user input
        if dia.exec():
            selected_items = []
            for i in range(items_length):
                if dia.items[i].isChecked():
                    selected_items.append(list(items)[i])
            return selected_items
    else:
        # set up a dialog template
        dialog_template = QtWidgets.QInputDialog()
        if prompt_type == "text" or prompt_type == "items":
            dialog_template.setInputMode(QtWidgets.QInputDialog.InputMode.TextInput)
        elif prompt_type == "number":
            dialog_template.setInputMode(QtWidgets.QInputDialog.InputMode.DoubleInput)
        else:
            raise Exception(f"Invalid prompt type: {prompt_type}")
        dialog_template.setWindowTitle(property_name)
        dialog_template.setLabelText(description)
        dialog_template.setOkButtonText(okText)
        dialog_template.setCancelButtonText(cancelText)
        dialog_template.setDoubleMaximum(1000000)
        dialog_template.setDoubleDecimals(2)
        if prompt_type == "items":
            dialog_template.setComboBoxItems(items)
            dialog_template.setComboBoxEditable(can_add_items)

        # retrieving user input
        if dialog_template.exec_():
            if prompt_type == "text" or prompt_type == "items":
                return dialog_template.textValue()
            elif prompt_type == "number":
                return dialog_template.doubleValue()

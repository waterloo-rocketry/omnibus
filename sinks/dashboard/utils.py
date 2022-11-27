from pyqtgraph.Qt import QtWidgets


def prompt_user(widget, property_name, description, prompt_type, items=None, can_add_items=False, okText="OK", cancelText="Cancel"):
    """
    Opens a pop up asking user for input.
    Returns None if input selection is not valid or user cancels
    """

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
    if dialog_template.exec_() == QtWidgets.QDialog.Accepted:
        if prompt_type == "text" or prompt_type == "items":
            return dialog_template.textValue()
        elif prompt_type == "number":
            return dialog_template.doubleValue()

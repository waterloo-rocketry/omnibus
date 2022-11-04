from pyqtgraph.Qt import QtWidgets

def prompt_user(widget, property_name, description, prompt_type, items=None, can_add_items = False):
    """
    Opens a pop up asking user for input. Returns None if input selection
    is not valid or user cancels
    """
    ok = False
    selection = None

    if prompt_type == "items":
        if (items == None):
            return None

        selection, ok = QtWidgets.QInputDialog.getItem(widget, property_name, description, items, 0, can_add_items)    
        
    elif prompt_type == "text":
        selection, ok = QInputDialog.getText(widget, property_name, description)

    elif prompt_type == "number":
        selection, ok = QInputDialog.getDouble(widget, property_name, description)

    if not ok:
        return None

    return selection
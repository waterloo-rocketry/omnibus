from dataclasses import dataclass
from typing import Optional
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtCore import Qt, Signal, QEvent, QObject


class EventTracker(QObject):
    """
    PyQt implements the observer pattern to communicate state changes between widgets.
    Signals are emitted by a widget (subject) and connected widget slots can listen in (observer).
    For example, a QPushButton emits a clicked() signal when it is activated by the mouse, spacebar,
    or keyboard shortcut and a QLabel can connect to this signal with a slot to update its text.
    More info about this: https://doc.qt.io/qtforpython/overviews/signalsandslots.html

    Unfortuantely, PyQt provides a limited amount of signals and since we use signals
    quite freqently, it would be nice to centeralize everything in one class.
    """
    # Key presses
    backspace_pressed = Signal(QtWidgets.QWidget)
    tab_pressed = Signal(QtWidgets.QWidget)
    reverse_tab_pressed = Signal(QtWidgets.QWidget)
    text_entered = Signal()
    zoom_in = Signal()
    zoom_out = Signal()
    zoom_reset = Signal()

    def eventFilter(self, widget, event):
        """
        If we want the filter the event out ie. stop it from being further handled, return true.
        We can also not handle the event by passing it to the base class.
        """
        if event.type() == QEvent.KeyPress:
            print("utils", widget, event)
            key_press = KeyEvent(event.key(), event.modifiers(), event.text())
            match key_press:
                case KeyEvent(Qt.Key_Backspace, _, _):
                    self.backspace_pressed.emit(widget)
                case KeyEvent(Qt.Key_Backtab, _, _):
                    print("back tabbing")
                    self.reverse_tab_pressed.emit(widget)
                case KeyEvent(Qt.Key_Tab, _, _):
                    print("tabing")
                    self.tab_pressed.emit(widget)
                case KeyEvent(Qt.Key_Equal, Qt.ControlModifier, _):
                    self.zoom_in.emit()
                case KeyEvent(Qt.Key_Minus, Qt.ControlModifier, _):
                    self.zoom_out.emit()
                case KeyEvent(Qt.Key_0, Qt.ControlModifier, _):
                    self.zoom_reset.emit()
                case _:
                    self.text_entered.emit()
        return super().eventFilter(widget, event)

@dataclass
class KeyEvent:
    key_code: int
    modifiers: int
    text: Optional[str]


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

        # set up separate plot checkbox
        self.checkbox_separate = QtWidgets.QCheckBox("Plot Separately")
        self.checkbox_separate.setChecked(True)
        self.layout.addWidget(self.checkbox_separate)
        self.layout.setAlignment(self.checkbox_separate, Qt.AlignRight)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)


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


def prompt_user(widget, property_name, description, prompt_type, items=None, can_add_items=False, okText="OK", cancelText="Cancel"):
    """
    Opens a pop up asking user for input.
    Returns None if input selection is not valid or user cancels
    """
    if prompt_type == "checkbox":
        # set up a checkbox dialog
        dia = CheckBoxDialog(property_name, description, items, widget)
        # retrieve user input
        if dia.exec():
            selected_items = []
            for i, item in enumerate(items):
                if dia.items[i].isChecked():
                    selected_items.append(item)

            return [selected_items, dia.checkbox_separate.isChecked()]
        return None

    # if prompt_type is text/items/number
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

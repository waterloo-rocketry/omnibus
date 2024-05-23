from dataclasses import dataclass
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
    enter_pressed = Signal()
    zoom_in = Signal()
    zoom_out = Signal()
    zoom_reset = Signal()
    save_file_keys_pressed = Signal()

    def eventFilter(self, widget, event):
        """
        After we intercept the event, propagate it down the event
        chain so that we don't disturb any default behaviours or return True
        if we don't want any widgets to further handle the event.
        """
        if event.type() == QEvent.KeyPress:
            key_press = KeyEvent(event.key(), event.modifiers())
            match key_press:
                case KeyEvent(Qt.Key_Backspace, _) | KeyEvent(Qt.Key_Delete, _):
                    self.backspace_pressed.emit(widget)
                case KeyEvent(Qt.Key_Backtab, _):
                    self.reverse_tab_pressed.emit(widget)
                case KeyEvent(Qt.Key_Tab, _):
                    self.tab_pressed.emit(widget)
                case KeyEvent(Qt.Key_Enter, _) | KeyEvent(Qt.Key_Return, _):
                    self.enter_pressed.emit()
                case KeyEvent(Qt.Key_Equal, Qt.ControlModifier):
                    self.zoom_in.emit()
                case KeyEvent(Qt.Key_Minus, Qt.ControlModifier):
                    self.zoom_out.emit()
                case KeyEvent(Qt.Key_0, Qt.ControlModifier):
                    self.zoom_reset.emit()
                case KeyEvent(Qt.Key_S, Qt.ControlModifier):  # Handle Ctrl+S
                    self.save_file_keys_pressed.emit()
        return super().eventFilter(widget, event)


@dataclass
class KeyEvent:
    key_code: int
    modifiers: int


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

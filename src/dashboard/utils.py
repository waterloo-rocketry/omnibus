from dataclasses import dataclass
from typing import Any, cast
from pyqtgraph.Qt import QtWidgets
from pyqtgraph.Qt.QtCore import Qt, QEvent, QObject
from pyqtgraph.Qt.QtCore import Signal as _Signal  # pyright: ignore[reportUnknownVariableType]
from pyqtgraph.Qt.QtGui import QKeyEvent

Signal = cast(Any, _Signal)


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
    backspace_pressed: Any = Signal(QtWidgets.QWidget)  # pyright: ignore[reportUnknownMemberType]
    tab_pressed: Any = Signal(QtWidgets.QWidget)  # pyright: ignore[reportUnknownMemberType]
    reverse_tab_pressed: Any = Signal(QtWidgets.QWidget)  # pyright: ignore[reportUnknownMemberType]
    enter_pressed: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    zoom_in: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    zoom_out: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    zoom_reset: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    save_file_keys_pressed: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    save_as_file_keys_pressed: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    open_file_keys_pressed: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    duplicate: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    lock_dashboard: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    lock_selected: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    send_forward: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    send_backward: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    send_to_front: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    send_to_back: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    remove_all: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    mouse_resize: Any = Signal()  # pyright: ignore[reportUnknownMemberType]
    escape_pressed: Any = Signal(QtWidgets.QWidget)  # pyright: ignore[reportUnknownMemberType]

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        """
        After we intercept the event, propagate it down the event
        chain so that we don't disturb any default behaviours or return True
        if we don't want any widgets to further handle the event.
        """

        if isinstance(event, QKeyEvent) and (
            event.type() == QEvent.Type.KeyPress
            or (event.type() == QEvent.Type.ShortcutOverride and event.key() == Qt.Key.Key_Backspace)
        ):
            key_press = KeyEvent(event.key(), event.modifiers())
            match key_press:
                case KeyEvent(Qt.Key.Key_Backspace, _) | KeyEvent(Qt.Key.Key_Delete, _):
                    self.backspace_pressed.emit(watched)
                case KeyEvent(Qt.Key.Key_Backtab, _):
                    self.reverse_tab_pressed.emit(watched)
                case KeyEvent(Qt.Key.Key_Tab, _):
                    self.tab_pressed.emit(watched)
                case KeyEvent(Qt.Key.Key_Enter, _) | KeyEvent(Qt.Key.Key_Return, _):
                    self.enter_pressed.emit()
                case KeyEvent(Qt.Key.Key_Equal, Qt.KeyboardModifier.ControlModifier):
                    self.zoom_in.emit()
                case KeyEvent(Qt.Key.Key_Minus, Qt.KeyboardModifier.ControlModifier):
                    self.zoom_out.emit()
                case KeyEvent(Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier):
                    self.zoom_reset.emit()
                case KeyEvent(Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier):
                    self.save_file_keys_pressed.emit()
                case KeyEvent(Qt.Key.Key_S, modifiers) if (modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier)) == (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier):
                    self.save_as_file_keys_pressed.emit()
                case KeyEvent(Qt.Key.Key_O, Qt.KeyboardModifier.ControlModifier):
                    self.open_file_keys_pressed.emit()
                case KeyEvent(Qt.Key.Key_D, Qt.KeyboardModifier.ControlModifier):
                    self.duplicate.emit()
                case KeyEvent(Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier):
                    self.lock_dashboard.emit()
                case KeyEvent(Qt.Key.Key_L):
                    self.lock_selected.emit()
                case KeyEvent(Qt.Key.Key_BracketRight, Qt.KeyboardModifier.ControlModifier):
                    self.send_to_front.emit()
                case KeyEvent(Qt.Key.Key_BracketRight):
                    self.send_forward.emit()
                case KeyEvent(Qt.Key.Key_BracketLeft, Qt.KeyboardModifier.ControlModifier):
                    self.send_to_back.emit()
                case KeyEvent(Qt.Key.Key_BracketLeft):
                    self.send_backward.emit()
                case KeyEvent(Qt.Key.Key_R, Qt.KeyboardModifier.ControlModifier):
                    self.remove_all.emit()
                case KeyEvent(Qt.Key.Key_M, Qt.KeyboardModifier.ControlModifier):
                    self.mouse_resize.emit()
                case KeyEvent(Qt.Key.Key_Escape, _):
                    self.escape_pressed.emit(watched)
                case _:
                    pass
        return super().eventFilter(watched, event)


@dataclass
class KeyEvent:
    key_code: int
    modifiers: Qt.KeyboardModifier


class ConfirmDialog(QtWidgets.QDialog):
    def __init__(self, property_name: str, description: str, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(property_name)

        self.buttonBox: QtWidgets.QDialogButtonBox = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok)
        self.buttonBox.accepted.connect(self.accept)

        self.main_layout: QtWidgets.QVBoxLayout = QtWidgets.QVBoxLayout()
        message = QtWidgets.QLabel(description)
        self.main_layout.addWidget(message)

        self.main_layout.addWidget(self.buttonBox)
        self.setLayout(self.main_layout)

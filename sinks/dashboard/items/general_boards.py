from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QApplication, QHeaderView, QItemDelegate, QAbstractItemView
from pyqtgraph.Qt.QtCore import Qt, QTimer, QEvent
from pyqtgraph.Qt.QtGui import QColorConstants
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 1  # time in seconds after which data "expires"

# proper way is to use QTableView and setModel(), but this is easier
class GBTableWidgetItem(QTableWidgetItem):
    def __init__(self):
        super().__init__()

        self.board = None
        self.path = None
        self.value = ''

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)
        self.expired_timeout.start(EXPIRED_TIME * 1000)

    def setData(self, role, data):
        super().setData(role, data)
        if role == Qt.EditRole:
            if not data:
                self.path = None
                self.value = ''
            elif data[0] == '=':
                # text starting with =, display text as is
                self.path = None
                self.value = data[1:]
                self.setForeground(QColorConstants.Black)
                self.expired_timeout.stop()
            else:
                # treat data as series path under board
                self.path = data
                self.value = ''
                self.resubscribe()

    def data(self, role):
        if role == Qt.DisplayRole:
            return self.value
        return super().data(role)

    def expire(self):
        self.setForeground(QColorConstants.Gray)
        pass

    def set_board(self, board):
        self.board = board
        self.resubscribe()

    def resubscribe(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        if self.board and self.path is not None:
            if self.path == '/':
                serie = self.board
            else:
                serie = f'{self.board}/{self.path}'
            publisher.subscribe(serie, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload

        if isinstance(data, int):
            self.value = f"{data:.0f}"
        elif isinstance(data, float):
            self.value = f"{data:.3f}"
        else:
            self.value = data

        self.setForeground(QColorConstants.Black)
        self.expired_timeout.stop()
        self.expired_timeout.start(EXPIRED_TIME * 1000)
        self.tableWidget().viewport().update()

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)

    # workaround for pyqt bug where reference is GC'd
    # introduces memory leak but should be fine as lone as it is triggered manually
    clones = []
    def clone(self):
        clone = GBTableWidgetItem()
        GBTableWidgetItem.clones.append(clone)
        return clone

class GBItemDelegate(QItemDelegate):
    def __init__(self, isboard, onchange=None):
        super().__init__()

        self.isboard = isboard
        self.onchange = onchange

    def createEditor(self, parent, option, index):

        items = sorted(set(s.split('/')[0] for s in publisher.get_all_streams()))

        editor = QComboBox(parent)
        editor.setEditable(True)
        editor.addItems(["test", "items"])

        if self.onchange:
            row = index.row()
            col = index.column()
            editor.currentTextChanged.connect(lambda text: self.onchange(row, col, text))

        return editor

    def eventFilter(self, editor, event):
        if (
            event.type() == QEvent.FocusOut and
            event.reason() in (Qt.PopupFocusReason, Qt.ActiveWindowFocusReason)
        ):
            return False
        return super().eventFilter(editor, event)

    def setEditorData(self, editor, index):
        editor.setCurrentText(index.data(Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole);

@Register
class GeneralBoardsItem(DashboardItem):
    def __init__(self, *args):
        # Call this in **every** dash item constructor
        super().__init__(*args)

        # Specify the layout
        self.layout = QHBoxLayout()
        self.setLayout(self.layout)

        self.parameters.param('rows').sigValueChanged.connect(self.on_rows_change)
        self.parameters.param('cols').sigValueChanged.connect(self.on_cols_change)

        self.widget = QTableWidget()
        self.widget.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.widget.setSelectionMode(QAbstractItemView.ContiguousSelection)
        self.widget.setItemPrototype(GBTableWidgetItem())
        self.widget.setItemDelegate(GBItemDelegate(False))
        self.widget.setItemDelegateForColumn(0, GBItemDelegate(True))
        self.layout.addWidget(self.widget)

        self.installEventFilter(self)

        self.update_size(self.parameters.param('rows').value(),
                         self.parameters.param('cols').value())

    def eventFilter(self, widget, event):
        if event.type() != QEvent.KeyPress or not (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            return False

        if event.key() == Qt.Key.Key_C:
            indexes = self.widget.selectedIndexes()

            minrow = min(i.row() for i in indexes)
            maxrow = max(i.row() for i in indexes)
            mincol = min(i.column() for i in indexes)
            maxcol = max(i.column() for i in indexes)

            copy = ''
            for i in range(minrow, maxrow+1):
                for j in range(mincol, maxcol+1):
                    copy += self.widget.item(i, j).data(Qt.EditRole) or ''
                    if j < maxcol: copy += '\t'
                if i < maxrow: copy += '\n'
            QApplication.clipboard().setText(copy)

            return True

        if event.key() == Qt.Key.Key_V:
            indexes = self.widget.selectedIndexes()
            if not indexes:
                minrow = mincol = 0
            else:
                minrow = min(i.row() for i in indexes)
                mincol = min(i.column() for i in indexes)

            paste = QApplication.clipboard().text()
            for i, row in enumerate(paste.split('\n')):
                for j, col in enumerate(row.split('\t')):
                    item = self.widget.item(minrow + i, mincol + j)
                    if item: item.setData(Qt.EditRole, col)

            return True

        return False

    def update_size(self, row, col):
        old = (self.widget.rowCount(), self.widget.columnCount())
        self.widget.setRowCount(row)
        self.widget.setColumnCount(col)

        self.resize(col * 107, row * 44)

    def add_parameters(self):
        return [
            {'name': 'rows', 'type': 'int', 'value': 3},
            {'name': 'cols', 'type': 'int', 'value': 5},
        ]

    def on_rows_change(self, _, rows):
        self.update_size(rows, self.widget.columnCount())

    def on_cols_change(self, _, cols):
        self.update_size(self.widget.rowCount(), cols)

    def on_delete(self):
        for i in range(self.widget.rowCount()):
            for j in range(1, self.widget.columnCount()):
                widget = self.widget.item(i, j)
                if widget: widget.on_delete()

    @staticmethod
    def get_name():
        return "General Boards"

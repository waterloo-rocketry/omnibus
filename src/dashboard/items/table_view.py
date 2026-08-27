import math
import json

from typing import Any, cast

from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, \
    QComboBox, QApplication, QHeaderView, QItemDelegate, QAbstractItemView, QSizePolicy
from pyqtgraph.Qt.QtCore import Qt, QTimer, QEvent, QByteArray
from pyqtgraph.Qt.QtGui import QColorConstants, QFocusEvent, QKeyEvent
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 2  # time in seconds after which data "expires"


def get_boards():
    series = publisher.get_all_streams()
    return sorted(set(s.split('/', 1)[0] for s in series))


def get_paths(board):
    if not board:
        return []

    def filter(s):
        if s.count('/') == 0:
            return '/'
        if s.startswith(board + '/'):
            return s.split('/', 1)[1]
        return None

    series = publisher.get_all_streams()
    paths = sorted(set(t for t in (filter(s) for s in series) if t))
    return paths or ['/']

# proper way is to use QTableView and setModel(), but this is easier


class TVTableWidgetItem(QTableWidgetItem):
    def __init__(self):
        super().__init__()

        self.board = None
        self.path = None
        self.value = ''
        self.first_col = True

        self.expired_timeout = QTimer()
        self.expired_timeout.setSingleShot(True)
        self.expired_timeout.timeout.connect(self.expire)

        # run post_init after the widget is added
        QTimer.singleShot(0, self.post_init)

    def post_init(self):
        try:
            tableWidget = self.tableWidget()
        except RuntimeError:
            self.on_delete()
            return

        if not tableWidget:
            return
        index = tableWidget.indexFromItem(self)
        if index and index.column() > 0:
            model = index.model()
            self.first_col = False
            self.board = model.data(model.index(index.row(), 0), Qt.ItemDataRole.EditRole)
            # rerun setData logic with updated values
            self.setData(Qt.ItemDataRole.EditRole, self.value)
        else:
            self.first_col = True

    def setData(self, role, value):
        super().setData(role, value)
        if role == Qt.ItemDataRole.EditRole:
            if not value:
                self.path = None
                self.value = ''
            elif value[0] == '=' or self.first_col:
                # display text as is
                self.path = None
                self.value = value
                self.setForeground(QColorConstants.Black)
                self.expired_timeout.stop()
            else:
                # treat data as series path under board
                self.path = value
                self.value = 'None'
                self.resubscribe()
                self.expired_timeout.start(EXPIRED_TIME * 1000)
            self.resubscribe()

    def data(self, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.value.removeprefix('=')
        return super().data(role)

    def expire(self):
        self.setForeground(QColorConstants.Gray)

    def set_board(self, board):
        self.board = board
        self.resubscribe()

    def resubscribe(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        if self.board and self.path is not None:
            if self.path == '/':
                serie = self.board
            else:
                serie = f'{self.board}/{self.path.strip("/")}'
            publisher.subscribe(serie, self.on_data_update)

    def on_data_update(self, _, payload):
        time, data = payload

        if isinstance(data, int):
            self.value = f"{data:.0f}"
        elif isinstance(data, float):
            self.value = f"{data:.3f}"
        else:
            self.value = str(data)

        self.setForeground(QColorConstants.Black)
        self.expired_timeout.start(EXPIRED_TIME * 1000)
        self.tableWidget().viewport().update()

    def on_delete(self):
        publisher.unsubscribe_from_all(self.on_data_update)
        self.expired_timeout.stop()

    # workaround for pyqt bug where reference ownership is not transferred and gets gc
    # this adds memory leak but should be fine as lone as it is triggered manually
    clones = []

    def clone(self):
        clone = TVTableWidgetItem()
        TVTableWidgetItem.clones.append(clone)
        return clone


class TVItemDelegate(QItemDelegate):
    def __init__(self, onchange=None):
        super().__init__()
        self.onchange = onchange

    def createEditor(self, parent, option, index):

        items = sorted(set(s.split('/')[0] for s in publisher.get_all_streams()))

        editor = QComboBox(parent)
        editor.setEditable(True)
        editor.setMaxVisibleItems(100)
        editor.view().setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)

        if index.column() == 0:  # first column, select board
            boards = get_boards()
            editor.addItems(boards)
        else:
            model = index.model()
            board = model.index(index.row(), 0).data(Qt.ItemDataRole.EditRole)
            paths = get_paths(board)
            editor.addItems(paths)

        if self.onchange:
            onchange = self.onchange
            row = index.row()
            col = index.column()
            editor.currentTextChanged.connect(lambda text: onchange(row, col, text))

        return editor

    def eventFilter(self, object, event):
        if (
            isinstance(event, QFocusEvent) and
            event.type() == QEvent.Type.FocusOut and
            event.reason() in (Qt.FocusReason.PopupFocusReason, Qt.FocusReason.ActiveWindowFocusReason)
        ):
            return False
        return super().eventFilter(object, event)

    def setEditorData(self, editor, index):
        cast(QComboBox, editor).setCurrentText(index.data(Qt.ItemDataRole.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, cast(QComboBox, editor).currentText(), Qt.ItemDataRole.EditRole)


@Register
class TableViewItem(DashboardItem):
    def __init__(self, dashboard, params=None):
        # Call this in **every** dash item constructor
        super().__init__(dashboard, params)

        # Specify the layout
        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        self.parameters.param('rows').sigValueChanged.connect(self.on_rows_change)
        self.parameters.param('cols').sigValueChanged.connect(self.on_cols_change)

        self.widget = QTableWidget()

        self.widget.setSelectionMode(QAbstractItemView.SelectionMode.ContiguousSelection)
        self.widget.setItemPrototype(TVTableWidgetItem())
        self.widget.setItemDelegate(TVItemDelegate(False))
        self.widget.setItemDelegateForColumn(0, TVItemDelegate(self.change_row_board))
        self.widget.verticalHeader().setSectionsMovable(True)

        hheader = self.widget.horizontalHeader()
        hheader.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        hheader.sectionResized.connect(self.update_size)

        self.main_layout.addWidget(self.widget)

        self.installEventFilter(self)

        self.on_rows_change(None, self.parameters.param('rows').value())
        self.on_cols_change(None, self.parameters.param('cols').value())

        if params:
            state = json.loads(params).get('table_view', {})
            hheader.restoreState(QByteArray.fromBase64(state.get('header_state').encode()))
            self.deserialize_range(state.get('cells'),
                                   0, self.widget.rowCount(),
                                   0, self.widget.columnCount())
            self.update_size()

    def eventFilter(self, watched, event):
        if not isinstance(event, QKeyEvent) or event.type() != QEvent.Type.KeyPress:
            return False

        indexes = self.widget.selectedIndexes()

        if indexes:
            minrow = min(i.row() for i in indexes)
            maxrow = max(i.row() for i in indexes)
            mincol = min(i.column() for i in indexes)
            maxcol = max(i.column() for i in indexes)
        else:
            minrow = maxrow = mincol = maxcol = 0

        # copy cells
        if event.key() == Qt.Key.Key_C and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if not indexes:
                return True
            QApplication.clipboard().setText(self.serialize_range(minrow, maxrow, mincol, maxcol))
            return True

        # paste cells
        if event.key() == Qt.Key.Key_V and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            self.deserialize_range(
                QApplication.clipboard().text(),
                minrow, maxrow, mincol, maxcol)
            return True

        # cut cells
        if event.key() == Qt.Key.Key_X and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            if not indexes:
                return True

            QApplication.clipboard().setText(self.serialize_range(minrow, maxrow, mincol, maxcol))

            for i in range(minrow, maxrow+1):
                for j in range(mincol, maxcol+1):
                    item = self.widget.item(i, j)
                    if item:
                        item.setData(Qt.ItemDataRole.EditRole, None)

            return True

        # delete cells
        if event.key() == Qt.Key.Key_Delete:
            if not indexes:
                return False

            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                # allow ctrl-delete to remove widget
                return False

            for i in range(minrow, maxrow+1):
                for j in range(mincol, maxcol+1):
                    item = self.widget.item(i, j)
                    if item:
                        item.setData(Qt.ItemDataRole.EditRole, None)

            return True

        return False

    def serialize_range(self, minrow, maxrow, mincol, maxcol):

        def get_item_data(row, col):
            item = self.widget.item(row, col)
            return item and item.data(Qt.ItemDataRole.EditRole) or ''

        return '\n'.join(
            '\t'.join(
                get_item_data(i, j)
                for j in range(mincol, maxcol+1))
            for i in range(minrow, maxrow+1))

    def deserialize_range(self, data, minrow, maxrow, mincol, maxcol):
        if not data:
            return

        lines = data.split('\n')

        for h in range(math.ceil((maxrow - minrow + 1) / len(lines))):
            for i, line in enumerate(lines):

                row = minrow + h * len(lines) + i
                if row > self.widget.rowCount():
                    break

                cells = line.split('\t')
                for j in range(math.ceil((maxcol - mincol + 1) / len(cells))):
                    for k, cell in enumerate(cells):
                        col = mincol + j * len(cells) + k
                        if col > self.widget.columnCount():
                            break

                        item = self.widget.item(row, col)
                        if not item:
                            item = TVTableWidgetItem()
                            self.widget.setItem(row, col, item)
                        item.setData(Qt.ItemDataRole.EditRole, cell)

    def update_size(self):
        row = self.widget.rowCount()
        col = self.widget.columnCount()

        width = sum(self.widget.columnWidth(i) for i in range(col)) + 50
        height = sum(self.widget.rowHeight(j) for j in range(row)) + 50

        self.parameters.param('width').setValue(width)
        self.parameters.param('height').setValue(height)

        self.resize(width, height)

    def add_parameters(self) -> list[Any]:
        return [
            {'name': 'rows', 'type': 'int', 'value': 3},
            {'name': 'cols', 'type': 'int', 'value': 5},
        ]

    def change_row_board(self, row, col, text):
        for i in range(1, self.widget.columnCount()):
            item = self.widget.item(row, i)
            if isinstance(item, TVTableWidgetItem):
                item.set_board(text)

    def on_rows_change(self, _, rows):
        oldrow = self.widget.rowCount()
        self.widget.setRowCount(rows)
        self.update_size()

    def on_cols_change(self, _, cols):
        self.widget.setColumnCount(cols)
        self.update_size()

    def on_delete(self):
        for i in range(self.widget.rowCount()):
            for j in range(1, self.widget.columnCount()):
                widget = self.widget.item(i, j)
                if isinstance(widget, TVTableWidgetItem):
                    widget.on_delete()

    def get_serialized_parameters(self):
        params: dict[str, Any] = self.parameters.saveState(filter='user')
        params['table_view'] = {
            'cells': self.serialize_range(
                0, self.widget.rowCount(),
                0, self.widget.columnCount()),
            'header_state': bytes(self.widget.horizontalHeader().saveState().toBase64().data()).decode(),
        }
        return json.dumps(params)

    @staticmethod
    def get_name():
        return "Table View"

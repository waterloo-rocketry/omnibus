from pyqtgraph.Qt.QtWidgets import QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QApplication, QHeaderView
from pyqtgraph.Qt.QtCore import Qt, QTimer, QEvent
from pyqtgraph.Qt.QtGui import QColorConstants
from pyqtgraph.parametertree.parameterTypes import ListParameter

from publisher import publisher
from .dashboard_item import DashboardItem
from .registry import Register

EXPIRED_TIME = 1  # time in seconds after which data "expires"

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
                self.path = None
                self.value = data[1:]
            else:
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

        def add_dropdown(r):
            def onchange(board):
                for j in range(1, self.widget.columnCount()):
                    self.widget.item(r, j).set_board(board)

            dropdown = QComboBox()
            dropdown.currentTextChanged.connect(onchange)
            dropdown.addItems([''] + sorted(set(s.split('/')[0] for s in publisher.get_all_streams())))
            self.widget.setCellWidget(r, 0, dropdown)

        if row > old[0]:
            for i in range(old[0], row):
                for j in range(1, col):
                    self.widget.setItem(i, j, GBTableWidgetItem())
                add_dropdown(i)

        if col > old[1]:
            for i in range(row):
                for j in range(max(old[1], 1), col):
                    self.widget.setItem(i, j, GBTableWidgetItem())
                if old[1] < 1:
                    add_dropdown(i)

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
                self.widget.item(i, j).on_delete()

    @staticmethod
    def get_name():
        return "General Boards"

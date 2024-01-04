from PyQt5.QtWidgets import QApplication, QComboBox, QVBoxLayout, QWidget

class CheckableComboBoxExample(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.checkable_combo = QComboBox()
        self.checkable_combo.addItems(["Option 1", "Option 2", "Option 3", "Option 4"])
        self.checkable_combo.setEditable(True)
        self.checkable_combo.setMaxVisibleItems(3)
        self.checkable_combo.view().pressed.connect(self.handle_item_clicked)

        layout.addWidget(self.checkable_combo)
        self.setLayout(layout)

    def handle_item_clicked(self, index):
        item = self.checkable_combo.model().itemFromIndex(index)
        if item.checkState() == 0:
            item.setCheckState(2)
        else:
            item.setCheckState(0)

def main():
    app = QApplication([])

    window = CheckableComboBoxExample()
    window.show()

    app.exec()

if __name__ == '__main__':
    main()



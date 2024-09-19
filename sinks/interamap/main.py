from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from src.main_window import MapWindow
import sys

def load_stylesheet(file_name):
    """Load QSS stylesheet from the provided file."""
    with open(file_name, "r") as file:
        return file.read()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Load and apply QSS stylesheet
    stylesheet = load_stylesheet("resources/styles/lightmode.qss")
    app.setStyleSheet(stylesheet)

    window = MapWindow()
    window.show()
    sys.exit(app.exec())

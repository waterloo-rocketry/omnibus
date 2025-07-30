import signal
import sys
import os

from PySide6.QtWidgets import QApplication, QMessageBox
from tileserver import start_tileserver_with_docker, stop_tileserver
from src.main_window import MapWindow

from src.config import ONLINE_MODE, MBTILES_PATH
import subprocess

def confirm_quit():
    """Prompt the user with a confirmation dialog."""
    reply = QMessageBox.question(
        None,
        "Confirm Exit",
        "Are you sure you want to quit?",
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No,
    )
    return reply == QMessageBox.Yes

def handle_sigint(*args):
    """Handle Ctrl+C gracefully."""
    if confirm_quit():
        QApplication.quit()


def load_stylesheet(file_name):
    """Load QSS stylesheet from the provided file."""
    with open(file_name, "r") as file:
        return file.read()

def interamap_driver():
    # quit applicaiton from terminal
    signal.signal(signal.SIGINT, lambda *args: QApplication.quit())
    app = QApplication(sys.argv)

    # Get relative path to the file 
    path = os.path.dirname(os.path.realpath(__file__))
    
    if not ONLINE_MODE:
        try:
            start_tileserver_with_docker(MBTILES_PATH)
            app.aboutToQuit.connect(stop_tileserver)
        except Exception as e:
            print(f"Failed to start TileServer: {e}")

    # Load and apply QSS stylesheet
    stylesheet = load_stylesheet(path+"/resources/styles/lightmode.qss")
    app.setStyleSheet(stylesheet)

    window = MapWindow()

    # Override closeEvent to show confirm dialog
    def custom_close_event(event):
        if confirm_quit():
            event.accept()
        else:
            event.ignore()

    window.closeEvent = custom_close_event
    window.show()

    sys.exit(app.exec())

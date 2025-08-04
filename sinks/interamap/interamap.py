import signal
import sys
import os

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox
from tileserver import start_tileserver, stop_tileserver
from src.main_window import MapWindow

from config import ONLINE_MODE, MBTILES_PATH

should_force_close = False

def handle_sigint(window, *args):
    """Handle Ctrl+C gracefully."""
    global should_force_close
    print("Ctrl+C detected. Exiting gracefully...")
    if window.confirm_quit():
        should_force_close = True  # Tell the closeEvent not to prompt again
        QApplication.quit()


def load_stylesheet(file_name):
    """Load QSS stylesheet from the provided file."""
    with open(file_name, "r") as file:
        return file.read()

def interamap_driver():
    app: QApplication = QApplication(sys.argv)

    # Workaround: Allow Python to process signals while Qt is running
    timer = QTimer()
    timer.start(100)  # triggers every 100ms
    timer.timeout.connect(lambda: None)  # dummy function keeps event loop awake

    # Get relative path to the file 
    path = os.path.dirname(os.path.realpath(__file__))

    # Load and apply QSS stylesheet
    stylesheet = load_stylesheet(path+"/resources/styles/lightmode.qss")
    app.setStyleSheet(stylesheet)
    # Set application logo
    app.setWindowIcon(QIcon(path + "/resources/logo.png"))

    window = MapWindow()
    
    # Setup Offline TileServer if not in online mode
    if not ONLINE_MODE:
        try:
            start_tileserver(MBTILES_PATH)
            app.aboutToQuit.connect(stop_tileserver)
        except Exception as e:
            QMessageBox.warning(
                window,
                "TileServer Error",
                f"Failed to start TileServer:\n{e}\n\nThe map may not function correctly in offline mode.",
                QMessageBox.StandardButton.Ok
            )
            print(f"Failed to start TileServer: {e}")

    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, lambda *args: handle_sigint(window, *args))

    # Override closeEvent to show confirm dialog
    def custom_close_event(event):
        if should_force_close:
            event.accept()  # Allow close without asking
        elif window.confirm_quit():
            window.quit()
            event.accept()
        else:
            event.ignore()

    window.closeEvent = custom_close_event
    window.show()

    sys.exit(app.exec())

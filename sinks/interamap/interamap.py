import signal
import sys
import os

from PySide6.QtWidgets import QApplication
from src.main_window import MapWindow

from src.config import ONLINE_MODE, MBTILES_PATH
import subprocess

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
        # Start the tile server
        tileserver_process = subprocess.Popen(["python", "-m", "tileserver", MBTILES_PATH])
        app.aboutToQuit.connect(tileserver_process.terminate)

    # Load and apply QSS stylesheet
    stylesheet = load_stylesheet(path+"/resources/styles/lightmode.qss")
    app.setStyleSheet(stylesheet)

    window = MapWindow()
    window.show()
    sys.exit(app.exec())

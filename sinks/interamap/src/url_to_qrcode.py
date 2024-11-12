import qrcode
import sys
import webbrowser
import os

from PIL.ImageQt import QPixmap
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QLabel, QApplication, QVBoxLayout, QWidget
from sinks.interamap.config import TERMINAL_QR_CODE


def generate_qr_code(qr_code_url):
    # init qr code object
    qr = qrcode.QRCode(version=3, box_size=20, border=10, error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(qr_code_url)
    qr.make(fit=True)
    # save img
    filename = "qr_code.png"
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(filename)
    # Serve img in web-browser (backup)
    # webbrowser.open(f"file://{os.path.abspath(filename)}")

    if TERMINAL_QR_CODE:
        qr.print_ascii()
        exit(1)
    return filename


class QRCodeWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Generate QR code and load into a QPixmap
        filename = generate_qr_code(qr_code_url)
        self.pixmap = QPixmap(filename)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # init QLabel + Alignment of QWidget in center
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        central_widget.setLayout(layout)

        # Minimum size for the QR code image
        self.setMinimumSize(400, 400)
        self.minimum_width = 400
        self.minimum_height = 400

        # scaling pixmap with resizing of the window
        self.update_pixmap_size()

    def resizeEvent(self, event):
        # Update the pixmap size every time the window resizes
        self.update_pixmap_size()
        event.accept()

    def update_pixmap_size(self):
        # Size of QLabel to fit the image
        available_size = self.label.size()

        # Determining size wrt, minimums
        width = available_size.width()
        height = available_size.height()

        if width < self.minimum_width or height < self.minimum_height:
            width = self.minimum_width
            height = self.minimum_height
        # make a scaled copy
        scaled_pixmap = self.pixmap.scaled(width, height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        # replace original with scaled copy
        self.label.setPixmap(scaled_pixmap)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: qr-code.py <link>")
        sys.exit(1)
    qr_code_url = sys.argv[1]
    app = QApplication(sys.argv)
    viewer = QRCodeWindow()
    viewer.show()
    sys.exit(app.exec())

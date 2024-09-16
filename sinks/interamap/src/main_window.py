import geocoder
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QSizePolicy, QLineEdit, QLabel, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from src.map_view import MapView

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive Map with Folium")
        self.setGeometry(100, 100, 1200, 600)  # Set initial size of the window
        self.setWindowIcon(QIcon("resources/icons/rocket_icon.ico"))  # Set the app icon

        # Set up the central widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Main layout for the window (using QSplitter for 80% - 20% split)
        main_splitter = QSplitter(Qt.Horizontal, self.main_widget)
        main_layout = QHBoxLayout(self.main_widget)
        main_layout.addWidget(main_splitter)

        # Initialize the map view and set it to expand
        self.map_view = MapView(self)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Add the map view to the splitter
        main_splitter.addWidget(self.map_view)

        # Add the side toolbar layout (Vertical Layout inside QWidget)
        self.side_toolbar = QWidget(self)
        toolbar_layout = QVBoxLayout(self.side_toolbar)
        toolbar_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding
        toolbar_layout.setSpacing(10)  # Add some spacing between buttons

        # Custom Toggle Button for Dark Mode
        self.toggle_button = QPushButton(self)
        self.toggle_button.setCheckable(True)
        self.toggle_button.setIcon(QIcon("resources/icons/moon.png"))
        self.toggle_button.setStyleSheet(self.get_toggle_button_stylesheet(False))
        self.toggle_button.setFixedSize(60, 30)  # Set fixed size for the toggle button
        self.toggle_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Prevent the button from expanding
        self.toggle_button.clicked.connect(self.toggle_dark_mode)

        # Create a container layout to align the toggle button to the left
        toggle_container = QHBoxLayout()
        toggle_container.addWidget(self.toggle_button, alignment=Qt.AlignLeft)  # Align the button to the left
        toolbar_layout.addLayout(toggle_container)  # Add the container layout to the toolbar layout

        # Input fields for latitude and longitude
        self.lat_input = QLineEdit(self)
        self.lat_input.setPlaceholderText("Enter Latitude")
        toolbar_layout.addWidget(QLabel("Latitude:"))
        toolbar_layout.addWidget(self.lat_input)

        self.lon_input = QLineEdit(self)
        self.lon_input.setPlaceholderText("Enter Longitude")
        toolbar_layout.addWidget(QLabel("Longitude:"))
        toolbar_layout.addWidget(self.lon_input)

        # Add button to add marker at the specified coordinates
        add_marker_button = QPushButton("Add Marker", self)
        add_marker_button.clicked.connect(self.add_marker)
        toolbar_layout.addWidget(add_marker_button)

        # Add button to mark the current location
        mark_current_location_button = QPushButton("Mark Current Location", self)
        mark_current_location_button.clicked.connect(self.mark_current_location)
        toolbar_layout.addWidget(mark_current_location_button)

        # Add button to clear all markers
        clear_markers_button = QPushButton("Clear Markers", self)
        clear_markers_button.clicked.connect(self.clear_markers)
        toolbar_layout.addWidget(clear_markers_button)

        # Add the toolbar to the splitter
        main_splitter.addWidget(self.side_toolbar)

        # Set the sizes of the splitter to achieve an 80-20 ratio
        main_splitter.setSizes([800, 200])  # Adjust these values to set the initial sizes

    def toggle_dark_mode(self):
        """Toggle between Dark Mode and Light Mode."""
        if self.toggle_button.isChecked():
            # Switch to Dark Mode
            self.load_stylesheet("resources/styles/darkmode.qss")
            self.toggle_button.setIcon(QIcon("resources/icons/sun.png"))
            self.toggle_button.setStyleSheet(self.get_toggle_button_stylesheet(True))
            self.map_view.toggle_map_theme(True)  # Enable dark mode tiles for the map
        else:
            # Switch to Light Mode
            self.load_stylesheet("resources/styles/lightmode.qss")
            self.toggle_button.setIcon(QIcon("resources/icons/moon.png"))
            self.toggle_button.setStyleSheet(self.get_toggle_button_stylesheet(False))
            self.map_view.toggle_map_theme(False)  # Enable light mode tiles for the map

    def get_toggle_button_stylesheet(self, is_dark_mode):
        """Return the QSS stylesheet for the toggle button based on the mode."""
        if is_dark_mode:
            return """
                QPushButton {
                    background-color: #3c3c3c;
                    border: 2px solid #3c3c3c;
                    border-radius: 15px;
                    padding: 5px;
                    icon-size: 20px;
                }
                QPushButton:checked {
                    background-color: #1c1c1c;
                    border: 2px solid #1c1c1c;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #f1c40f;
                    border: 2px solid #f1c40f;
                    border-radius: 15px;
                    padding: 5px;
                    icon-size: 20px;
                }
                QPushButton:checked {
                    background-color: #f39c12;
                    border: 2px solid #f39c12;
                }
            """

    def load_stylesheet(self, stylesheet_path):
        """Load and apply the stylesheet from the provided path."""
        with open(stylesheet_path, "r") as file:
            self.setStyleSheet(file.read())

    def add_marker(self):
        """Function to add a marker on the map at specified coordinates."""
        try:
            lat = float(self.lat_input.text())
            lon = float(self.lon_input.text())
            self.map_view.add_marker_to_map([lat, lon], "New Marker", "red")
        except ValueError:
            print("Invalid input for latitude or longitude. Please enter valid numbers.")

    def mark_current_location(self):
        """Function to get the current location using geocoder and mark it on the map."""
        try:
            # Get the current location using geocoder (based on IP)
            g = geocoder.ip('me')
            if g.ok:
                lat, lon = g.latlng
                self.map_view.add_marker_to_map([lat, lon], "Current Location", "blue")
            else:
                print("Unable to determine current location.")
        except Exception as e:
            print(f"Error fetching current location: {e}")

    def clear_markers(self):
        """Function to clear all markers from the map."""
        self.map_view.clear_all_markers()

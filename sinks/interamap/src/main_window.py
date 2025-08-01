import os

from PySide6.QtWidgets import (
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    QLabel,
    QSplitter,
    QComboBox,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from src.map_view import MapView

from src.http_server import get_share_url, ThreadedHTTPServer
from src.url_to_qrcode import QRCodeWindow
from config import BoardID

class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.relative_path = os.path.dirname(
            os.path.dirname(os.path.realpath(__file__))
        )

        self.setWindowTitle("Interactive Map with Folium")
        self.setGeometry(100, 100, 1200, 600)  # Set initial size of the window

        self.data_sources = {
            value: key
            for key, value in enumerate(
            ["None", "Real-time Data Source", "Load KMZ File"]
            )
        }
        self.data_source = 0
        self.start_index_to_feature_ui = 3  # index to insert the feature of the data source ui, should use get_current_index_to_feature_ui() to get the index
        self.kmz_file_label = ""

        # Set up the central widget and layout
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Main layout for the window (using QSplitter for 80% - 20% split)
        self.main_splitter = QSplitter(Qt.Horizontal, self.main_widget)
        main_layout = QHBoxLayout(self.main_widget)
        main_layout.addWidget(self.main_splitter)

        # Set Light / Dark Mode
        self.mode = "light" # "light" or "dark"

        # Initialize the map view and set it to expand
        self.map_view = MapView(self)
        self.map_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.map_view.update_gps_label.connect(self.update_gps_status)
        self.map_view.point_storage.storage_update.connect(self.update_marker_button_states)

        # Add the map view to the splitter
        self.main_splitter.addWidget(self.map_view)

        self.init_side_toolbar()

        # Add the toolbar to the splitter
        self.main_splitter.addWidget(self.side_toolbar)

        # Set the sizes of the splitter to achieve an 80-20 ratio
        self.main_splitter.setSizes(
            [800, 200]
        )  # Adjust these values to set the initial sizes
        
        # Enable window dragging for frameless window
        self.old_pos = None
        
        # HTTP Share Server
        self.share_server = ThreadedHTTPServer(os.path.join(self.relative_path, "shared"))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() if hasattr(event, "globalPosition") else event.globalPos()
            delta = new_pos - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = new_pos

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    def init_side_toolbar(self):
        """Initialize the side toolbar with buttons and input fields."""
        # Add the side toolbar layout (Vertical Layout inside QWidget)
        self.start_index_to_feature_ui = 3
        self.side_toolbar = QWidget(self)
        self.toolbar_layout = QVBoxLayout(self.side_toolbar)
        self.toolbar_layout.setContentsMargins(10, 10, 10, 10)  # Add some padding
        self.toolbar_layout.setSpacing(20)  # Add some spacing between buttons

        # Custom Toggle Button for Dark Mode
        self.toggle_button = QPushButton(self)
        self.initial_toggle_mode_button()
        self.toggle_button.setFixedSize(80, 30)  # Set fixed size for the toggle button
        self.toggle_button.setSizePolicy(
            QSizePolicy.Fixed, QSizePolicy.Fixed
        )  # Prevent the button from expanding
        self.toggle_button.clicked.connect(self.toggle_dark_mode)

        # Create a container layout to align the toggle button to the left
        self.top_bar = QVBoxLayout()
        self.top_bar.addWidget(
            self.toggle_button, alignment=Qt.AlignLeft
        )  # Align the button to the left
        self.toolbar_layout.addLayout(
            self.top_bar
        )  # Add the container layout to the toolbar layout

        # Add a label to indicate the data source selection section
        self.data_source_label = QLabel("Data Source:")
        self.toolbar_layout.addWidget(self.data_source_label)
        
        # Add a combo box to choose the data source
        self.data_source_ui = QComboBox(self)
        self.data_source_ui.addItem("None")
        self.data_source_ui.addItem("Real-time Data Source")
        self.data_source_ui.addItem("Load KMZ File")
        self.data_source_ui.setCurrentIndex(self.data_source)
        self.data_source_ui.currentIndexChanged.connect(self.toggle_data_source)
        self.toolbar_layout.addWidget(self.data_source_ui)

        # Tool only for Real-time Data Source
        if self.data_source == 1:

            # Add a label to indicate the map markers operator section
            self.map_markers_label = QLabel("Map Markers:")
            self.toolbar_layout.addWidget(self.map_markers_label)

            # Start Share Server button and another button to show qr code
            share_server_layout = QHBoxLayout()
            share_server_label_layout = QHBoxLayout()

            share_server_label = QLabel("Share Server:")
            self.share_server_status_label = QLabel("Share Server Stopped")
            self.start_share_server_button = QPushButton("Start Share Server", self)

            share_server_label_layout.addWidget(share_server_label)
            self.share_server_status_label.setStyleSheet("color: red")
            share_server_label_layout.addWidget(self.share_server_status_label)
            self.toolbar_layout.addLayout(share_server_label_layout)

            self.start_share_server_button.clicked.connect(self.toggle_http_server)
            share_server_layout.addWidget(self.start_share_server_button)
            
            self.show_qr_code_button = QPushButton("Show QR Code", self)
            self.show_qr_code_button.clicked.connect(self.show_qr_code)
            self.show_qr_code_button.setDisabled(True)
            self.show_qr_code_button.setStyleSheet("color: grey")
            share_server_layout.addWidget(self.show_qr_code_button)
            
            self.toolbar_layout.addLayout(share_server_layout)

        self.toolbar_layout.addStretch(1)

        # Group marker-related actions in a horizontal layout for better UX
        marker_actions_layout = QHBoxLayout()

        # Center markers button
        self.center_markers_button = QPushButton("Refresh Map", self)
        self.center_markers_button.setToolTip("Center the map view on all markers")
        self.center_markers_button.clicked.connect(self.map_view.refresh_map)
        marker_actions_layout.addWidget(self.center_markers_button)

        # Clear markers button
        self.clear_markers_button = QPushButton("Clear Markers", self)
        self.clear_markers_button.setToolTip("Remove all markers from the map")
        self.clear_markers_button.clicked.connect(self.clear_markers)
        marker_actions_layout.addWidget(self.clear_markers_button)

        # Export markers button
        self.export_points_button = QPushButton("Export to KMZ", self)
        self.export_points_button.setToolTip("Export all markers to a KMZ file")
        self.export_points_button.clicked.connect(self.map_view.point_storage.export_points)
        marker_actions_layout.addWidget(self.export_points_button)

        self.update_marker_button_states()

        # Add the horizontal layout to the toolbar
        self.toolbar_layout.addLayout(marker_actions_layout)
        
        return self.side_toolbar
    
    def update_gps_status(self, gps_status):
        # Slot to handle the update for MainWindow's label
        self.gps_status_label.setText(gps_status)

    def get_current_index_to_feature_ui(self):
        self.start_index_to_feature_ui += 1
        return self.start_index_to_feature_ui - 1
    
    def toggle_http_server(self):
        self.share_server.toggle()
        
        if self.share_server.get_status():
            self.start_share_server_button.setText("Stop Share Server")
            self.share_server_status_label.setText("Share Server Running")
            self.share_server_status_label.setStyleSheet("color: green")
            self.show_qr_code_button.setDisabled(False)
            self.show_qr_code_button.setStyleSheet("")
        else:
            self.share_server_status_label.setText("Share Server Stopped")
            self.share_server_status_label.setStyleSheet("color: red")
            self.show_qr_code_button.setDisabled(True)
            self.show_qr_code_button.setStyleSheet("color: grey")

    def toggle_data_source(self):
        """Toggle between None, Real-time Data Source, and Load KMZ File."""

        # enum for data sources
        self.data_source = self.data_sources.get(self.data_source_ui.currentText())
        self.reset_data_source_ui()

        if self.map_view.rt_parser.running:
            self.map_view.stop_realtime_data()
            self.map_view.refresh_map() # Refresh the map to clear real-time layers

        if self.data_source == 1:  # Real-time Data Source
            # if is real-time data source selected, then add the following

            # Display GPS satellite connection status (satellite number and quality)
            self.map_view.start_stop_realtime_data()
            self.gps_status_label = QLabel("GPS Status: Not Connected")
            self.gps_status_label.setFixedWidth(200)  # Set fixed width for the label
            self.gps_status_label.setSizePolicy(
                QSizePolicy.Fixed, QSizePolicy.Fixed
            )
            self.gps_status_label.setWordWrap(True)
            self.gps_status_label.setStyleSheet(
                "border: 1px solid #888; border-radius: 5px; padding: 4px;"
            )
            self.toolbar_layout.insertWidget(self.get_current_index_to_feature_ui()-2, self.gps_status_label)
            
            start_stop_button = QPushButton("Start Real-time Parser", self)
            start_stop_button.setStyleSheet("")
            def toggle_parser():
                previous_state = self.map_view.rt_parser.running
                self.map_view.start_stop_realtime_data()
                running = self.map_view.rt_parser.running
                if previous_state is False and running is False:
                    QMessageBox.warning(self, "No Connection", "No real-time data connection established yet.")
                if running:
                    start_stop_button.setText("Stop Real-time Parser")
                    start_stop_button.setStyleSheet("background-color: #f1c40f; color: black;")
                else:
                    start_stop_button.setText("Start Real-time Parser")
                    start_stop_button.setStyleSheet("")
            start_stop_button.clicked.connect(toggle_parser)
            # Set initial state
            if self.map_view.rt_parser.running:
                start_stop_button.setText("Stop Real-time Parser")
                start_stop_button.setStyleSheet("background-color: #f1c40f; color: black;")
            else:
                start_stop_button.setText("Start Real-time Parser")
                start_stop_button.setStyleSheet("")

            self.toolbar_layout.insertWidget(
                self.start_index_to_feature_ui, start_stop_button
            )

            data_options = ["All"] + [board.value for board in BoardID]
            data_combo = QComboBox(self)
            data_combo.addItems(data_options)
            data_combo.currentTextChanged.connect(self.map_view.change_data_source)
            self.toolbar_layout.insertWidget(
                self.get_current_index_to_feature_ui(), QLabel("Sources Options:")
            )
            self.toolbar_layout.insertWidget(
                self.get_current_index_to_feature_ui(), data_combo
            )

        elif self.data_source == 2:  # Load KMZ File
            # if is load KMZ file selected, then add the following
            load_kmz_button = QPushButton("Load KMZ File", self)
            load_kmz_button.clicked.connect(self.load_kmz_file)
            self.toolbar_layout.insertWidget(
                self.get_current_index_to_feature_ui(),
                QLabel("KMZ File:" + self.kmz_file_label),
            )
            self.toolbar_layout.insertWidget(
                self.get_current_index_to_feature_ui(), load_kmz_button
            )

    def reset_data_source_ui(self):
        """Reset the data source UI to default state."""

        # reset the data source UI to default state
        self.init_side_toolbar()
        self.main_splitter.replaceWidget(1, self.side_toolbar)

    def load_kmz_file(self):
        """Function to load a KMZ file and display it on the map."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open KMZ File", "", "KMZ Files (*.kmz)"
        )
        if file_path:
            self.kmz_file_label = file_path  # TODO: Update the label with the file name
            self.map_view.load_kmz_file(file_path)

    def toggle_dark_mode(self):
        self.mode = "dark" if self.mode=="light" else "light"
        self.initial_toggle_mode_button()

    def initial_toggle_mode_button(self):
        """Toggle between Dark Mode and Light Mode."""
        if self.mode == "dark":
            # Switch to Dark Mode
            self.load_stylesheet(self.relative_path + "/resources/styles/darkmode.qss")
            self.toggle_button.setText("Dark")
            self.toggle_button.setStyleSheet(self.get_toggle_button_stylesheet(True))
            self.map_view.toggle_map_theme(True)  # Enable dark mode tiles for the map
        else:
            # Switch to Light Mode
            self.load_stylesheet(self.relative_path + "/resources/styles/lightmode.qss")
            self.toggle_button.setText("Light")
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
            print(
                "Invalid input for latitude or longitude. Please enter valid numbers."
            )

    def update_marker_button_states(self):
        """Update marker button states based on available markers."""
        has_markers = (self.map_view.point_storage.get_gps_points() or 
                    self.map_view.point_storage.get_linestring_gps())
        self.clear_markers_button.setEnabled(bool(has_markers))
        self.export_points_button.setEnabled(bool(has_markers))
        self.center_markers_button.setEnabled(bool(has_markers))

        # Update styles based on enabled state
        def set_button_style(button):
            if button.isEnabled():
                button.setStyleSheet("")
            else:
                button.setStyleSheet("background-color: grey; color: white;")

        set_button_style(self.clear_markers_button)
        set_button_style(self.export_points_button)
        set_button_style(self.center_markers_button)

    def clear_markers(self):
        """Function to clear all markers from the map."""
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Are you sure you want to clear all markers?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        self.map_view.clear_all_markers()

    def show_qr_code(self):
        """Function to display the QR code for the shared server URL."""
        qr_window = QRCodeWindow(get_share_url())
        qr_window.show()

    def confirm_quit(self) -> bool:
        """Prompt the user with a confirmation dialog."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to quit?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        return reply == QMessageBox.Yes

    def quit(self):
        self.map_view.quit()
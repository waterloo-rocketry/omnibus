import folium
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QSizePolicy

class MapView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Set the size policy to make the widget expand to fill space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)  # Allow it to shrink completely

        # Initialize a list to store added markers
        self.markers = []

        # Initialize the map with a default tile style
        self.is_dark_mode = False
        self.create_online_map()

    def create_online_map(self):
        """Create a folium map with the current tile style."""
        tiles = "cartodbpositron" if not self.is_dark_mode else "cartodbdark_matter"  # Light and dark tiles
        self.m = folium.Map(
            location=[43.4643, -80.5204],  # Center of the map
            zoom_start=12,
            tiles=tiles,  # Set the tile style dynamically
            width='100%',  # Ensure map width is 100%
            height='100%'  # Ensure map height is 100%
        )
        
        # Add a default marker to the map
        folium.Marker(
            location=[43.4643, -80.5204],
            popup="Waterloo, ON",
            icon=folium.Icon(color="blue", icon="info-sign"),
        ).add_to(self.m)

        # Save the folium map to an HTML string with a responsive style
        self.update_map()

    def update_map(self):
        """Renders the map and updates the QWebEngineView."""
        self.map_html = self.m.get_root().render().replace(
            '<div style="width:100%;height:100%"></div>',
            '<div style="width:100%;height:100%;position:absolute;top:0;bottom:0;right:0;left:0;"></div>'
        )
        self.setHtml(self.map_html)

    def add_marker_to_map(self, location, popup_text, color):
        """Add a marker to the map and update the view."""
        marker = folium.Marker(
            location=location,
            popup=popup_text,
            icon=folium.Icon(color=color, icon="info-sign"),
        )
        self.markers.append(marker)
        marker.add_to(self.m)
        self.update_map()

    def clear_all_markers(self):
        """Clear all markers from the map."""
        self.create_online_map()
        self.markers.clear()

    def toggle_map_theme(self, is_dark_mode):
        """Toggle the map theme between light and dark mode."""
        self.is_dark_mode = is_dark_mode
        self.create_online_map()

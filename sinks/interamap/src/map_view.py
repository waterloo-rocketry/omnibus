from config import ONLINE_MODE

from typing import List

from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QSizePolicy

from src.gps_cache import GPS_Cache
from src.real_time_parser import RTParser

import time

import flask

import threading

import logging

if not ONLINE_MODE:
    """
    Need to run the following command to download required js and css files (only once, with internet connection):
    $ python -m offline_folium
    """
    import offline_folium
import folium

from folium.plugins import Realtime
from fastkml import kml

from src.kmz_parser import KMZParser
from src.data_struct import Point_GPS, LineString_GPS

from src.tools.current_location import get_current_location


class MapView(QWebEngineView):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Online Mode
        self.online = ONLINE_MODE

        self.kmz_parser = None

        self.coordinate = get_current_location()

        print("Online Mode:", self.online)

        # Set the size policy to make the widget expand to fill space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)  # Allow it to shrink completely

        # Initialize the map with a default tile style
        self.is_dark_mode = False

        # Initialize Real-time Parser and Real-time data handler
        self.rt_parser = RTParser()
        self.rt_parser.gps_RT_data.connect(self.storage_rt_info)

        # Initialize a Point Storage object to store GPS points
        self.point_storage = GPS_Cache()
        self.last_map_point_update = 0

        self.create_map()

    def __del__(self):
        self.rt_parser.stop()
        self.rt_parser.terminate()

    def create_map(self):
        """Create a folium map with the current tile style."""

        if self.kmz_parser is not None:
            self.coordinate = [
                self.kmz_parser.gps_data[0].lat,
                self.kmz_parser.gps_data[0].lon,
            ]

        if self.coordinate is None:
            self.coordinate = [43.4643, -80.5204]  # Default to Waterloo, Ontario

        self.m = folium.Map(
            location=self.coordinate,  # Center of the map
            zoom_start=12,
            tiles=None,  # Set the tile style dynamically
            width="100%",  # Ensure map width is 100%
            height="100%",  # Ensure map height is 100%
        )

        # Add a bottom layer with the default tile style (If online, it will use CartoDB tiles)
        folium.TileLayer(
            tiles=(
                "cartodbpositron" if not self.is_dark_mode else "cartodbdark_matter"
            ),  # Light and dark tiles
            attr="CartoDB",
            name="CartoDB",
            overlay=False,
        ).add_to(self.m)

        self.initialize_realtime_source()
        self.add_offline_layer()

        # For Debugging
        # self.m.save('offline_map.html')

        # Save the folium map to an HTML string with a responsive style
        self.update_map()

    def initialize_realtime_source_server(self, point_storage):
        app = flask.Flask(__name__)

        @app.route('/')
        def get_realtime_gps():

            point_id = 0

            response = flask.jsonify({
                'type': 'FeatureCollection',
                'features': [{
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [point.lon, point.lat]
                    },
                    'properties': {
                        'id': (point_id := point_id + 1)
                    }
                } for point in point_storage.get_gps_points()]
            })

            response.headers.add('Access-Control-Allow-Origin', '*')

            return response

        # Disable flask request logging
        logging.getLogger("werkzeug").disabled = True

        app.run(debug=False)

    def initialize_realtime_source(self):

        realtime_source_thread = threading.Thread(target=self.initialize_realtime_source_server, args=(self.point_storage,))
        realtime_source_thread.daemon = True
        realtime_source_thread.start()
        
        rt = Realtime("http://127.0.0.1:5000", point_to_layer=folium.JsCode("(f, coordinate) => { return L.circleMarker(coordinate, {radius: 3, fillOpacity: 1})}"), interval=100)
        rt.add_to(self.m)

    def add_offline_layer(self):
        """Add a offline tile layer to the map."""

        # Note: If local server is not running, and internet is available, it will use online tiles
        if not self.online:
            folium.TileLayer(
                tiles="http://localhost:8080/styles/basic-preview/{z}/{x}/{y}.png",
                attr="Local OSM Tiles",
                name="Local MBTiles",
                overlay=False,
            ).add_to(self.m)

    def update_map(self):
        self.draw_gps_data()
        """Renders the map and updates the QWebEngineView."""
        self.map_html = (
            self.m.get_root()
            .render()
            .replace(
                '<div style="width:100%;height:100%"></div>',
                '<div style="width:100%;height:100%;position:absolute;top:0;bottom:0;right:0;left:0;"></div>',
            )
        )
        self.setHtml(self.map_html)

    def add_marker_to_map(self, location, popup_text, color):
        """Add a marker to the map and update the view."""
        marker = folium.Marker(
            location=location,
            popup=popup_text,
            icon=folium.Icon(color=color, icon="info-sign"),
        )
        marker.add_to(self.m)
        self.update_map()

    def clear_all_markers(self):
        """Clear all markers from the map."""
        self.create_map()
        self.point_storage.clear_points()

    def toggle_map_theme(self, is_dark_mode):
        """Toggle the map theme between light and dark mode."""
        # Only working for online mode
        self.is_dark_mode = is_dark_mode
        self.create_map()

    def load_kmz_file(self, kmz_file_path):
        """Load a KMZ file and display the contents on the map."""
        self.kmz_parser = KMZParser(kmz_file_path)
        self.clear_all_markers()
        self.update_map()

    def start_stop_realtime_data(self):
        if not self.rt_parser.running:
            self.rt_parser.start()
        else:
            self.rt_parser.stop()
    
    def storage_rt_info(self, info): 

        if ("lat" in info.__dict__ and "lon" in info.__dict__ and time.time() - self.last_map_point_update >= 0.5):
            self.last_map_point_update = time.time()
            self.point_storage.store_info(info)
            
    def set_map_center(self, coord: List[float]):
        """Set the center of the map to the given latitude and longitude."""
        # self.create_map()
        self.add_marker_to_map(coord, "Current Location", "blue")

    def draw_gps_data(self):
        if self.kmz_parser is None:
            return
        total_points = len(self.kmz_parser.gps_data)
        step = max(total_points // 500, 1)  # Ensure at least one point is drawn

        for i in range(0, total_points, step):
            data = self.kmz_parser.gps_data[i]
            if isinstance(data, Point_GPS):
                folium.CircleMarker(
                    location=[data.lat, data.lon],
                    radius=3,  # Small radius for the marker
                    color="blue",
                    fill=True,
                    fill_color="blue",
                    popup=f"Height: {data.alt}m, Timestamp: {data.time_stamp}",
                ).add_to(self.m)
            elif isinstance(data, LineString_GPS):
                line = folium.PolyLine(
                    locations=[[point.lat, point.lon] for point in data.points],
                    color="red",
                )
                line.add_to(self.m)
            else:
                print("Unhandled data type:", type(data))

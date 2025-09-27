import logging
import random
import threading
import time
from typing import List

import flask
from PySide6.QtCore import Signal
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QSizePolicy

from config import ONLINE_MODE, ZOOM_MAX, ZOOM_MIN, ZOOM_DEFAULT, GRADIENT_COLORS
from src.gps_cache import GPS_Cache, Info_GPS
from src.real_time_parser import RTParser

if not ONLINE_MODE:
    """
    Need to run the following command to download required js and css files (only once, with internet connection):
    $ python -m offline_folium
    """
    from offline_folium import offline

import folium
from folium.plugins import Realtime
import branca.colormap as cm

from src.kmz_parser import KMZParser
from src.data_struct import Point_GPS, LineString_GPS
import os


class MapView(QWebEngineView):

    # Signal to update the label in the MainWindow
    update_gps_label = Signal(str)
    gradient_count = 0

    def __init__(self, parent=None):
        super().__init__(parent)

        # Online Mode
        self.online = ONLINE_MODE

        self.kmz_parser = None

        self.coordinate = None

        print("Online Mode:", self.online)

        # Set the size policy to make the widget expand to fill space
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(0, 0)  # Allow it to shrink completely

        # Initialize the map with a default tile style
        self.is_dark_mode = False

        # Initialize Real-time Parser and Real-time data handler
        self.rt_parser = RTParser()
        self.rt_parser.gps_RT_data.connect(self.storage_rt_info)
        # Avoid QThread Race Condition Issue cause MapView not updating
        self.rt_parser.state.connect(self.toggle_parse_state)
        self.parse_state = False

        # Initialize a Point Storage object to store GPS points
        self.point_storage = GPS_Cache()

        self.last_map_point_update = 0
        self.realtime_source_thread = None

        self.source: str | None = None

        self.initialize_realtime_source()  # For real-time update of GPS data

        self.refresh_map()

    def __del__(self):
        self.quit()

    def quit(self):
        self.stop_realtime_data()
        self.rt_parser.wait(1000) # join rt_parser thread with timeout of 1s

    def refresh_map(self):
        """Create a folium map with the current tile style."""

        if (self.point_storage.get_gps_points() and len(self.filter_point(self.point_storage.get_gps_points(), self.source)) > 5):
            self.coordinate = [
                sum(map(attr, random.sample(self.filter_point(self.point_storage.get_gps_points(), self.source), 5)))
                / 5
                for attr in [lambda p: p.lat, lambda p: p.lon]
            ]

        if self.coordinate is None:
            self.coordinate = [43.4643, -80.5204]  # Default to Waterloo, Ontario

        self.m = folium.Map(
            location=self.coordinate,  # Center of the map
            zoom_start=ZOOM_DEFAULT,  # Default zoom level
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
            max_native_zoom=ZOOM_MAX,
            max_zoom=ZOOM_MAX,
            min_zoom=ZOOM_MIN,
        ).add_to(self.m)

        self.add_offline_layer()

        self.update_map()

    def initialize_realtime_source_server(self):
        """Initialize a Flask server to serve real-time GPS data."""

        app = flask.Flask(__name__)

        @app.route("/")
        def get_realtime_gps():

            point_id = 0

            response = flask.jsonify(
                {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [point.lon, point.lat],
                            },
                            "properties": {"id": (point_id := point_id + 1)},
                        }
                        for point in self.filter_point(
                            self.point_storage.get_gps_points(), self.source
                        )
                    ],
                }
            )

            response.headers.add("Access-Control-Allow-Origin", "*")

            return response

        # Disable flask request logging
        logging.getLogger("werkzeug").disabled = True

        app.run(debug=False)

    def initialize_realtime_source(self):
        """Initialize real-time map updates from a Flask server."""

        if not self.realtime_source_thread:
            self.realtime_source_thread = threading.Thread(
                target=self.initialize_realtime_source_server
            )
            self.realtime_source_thread.daemon = True
            self.realtime_source_thread.start()

    def add_realtime_layer(self):
        rt = Realtime(
            "http://127.0.0.1:5000",
            point_to_layer=folium.JsCode(
                "(f, coordinate) => { return L.circleMarker(coordinate, {radius: 3, fillOpacity: 1})}"
            ),
            interval=100,
        )
        if not self.online:
            rt.default_js = [
                (
                    "Leaflet_Realtime_js",
                    os.path.join(
                        os.path.dirname(__file__), "static/leaflet-realtime.js"
                    ),
                )
            ]
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
        """Update the map with the current GPS data."""
        if self.parse_state:
            self.add_realtime_layer()
        else:
            self.draw_gps_data(
                self.filter_point(self.point_storage.get_gps_points(), self.source)
                + self.point_storage.get_linestring_gps()
            )

        self.map_html = (
            self.m.get_root()
            .render()
            .replace(
                '<div style="width:100%;height:100%"></div>',
                '<div style="width:100%;height:100%;position:absolute;top:0;bottom:0;right:0;left:0;"></div>',
            )
        )
        self.setHtml(self.map_html)

        # For Debugging
        # self.m.save('offline_map.html')

    def clear_all_markers(self):
        """Clear all markers from the map."""
        self.point_storage.clear_points()
        self.point_storage.clear_linestrings()
        self.refresh_map()

    def toggle_map_theme(self, is_dark_mode):
        """Toggle the map theme between light and dark mode."""
        # Only working for online mode
        self.is_dark_mode = is_dark_mode
        self.refresh_map()

    def load_kmz_file(self, kmz_file_path):
        """Load a KMZ file and display the contents on the map."""
        self.kmz_parser = KMZParser(kmz_file_path)
        self.clear_all_markers()
        self.point_storage.store_infos(self.kmz_parser.gps_data)
        self.refresh_map()

    def stop_realtime_data(self):
        self.emit_update_signal("Stopped")
        print("Stopping real-time data...")
        self.rt_parser.stop()

    def start_stop_realtime_data(self):
        if self.rt_parser.running:
            self.stop_realtime_data()
        else:
            self.rt_parser.start()
        self.refresh_map()

    def emit_update_signal(self, gps_text):
        # Emit the signal with the new text when the button is clicked
        self.update_gps_label.emit(f"GPS Status:\n\n{gps_text}")

    def storage_rt_info(self, info):
        self.point_storage.store_info(info)
        if isinstance(info, Info_GPS):
            self.emit_update_signal(
                f"Board ID: {info.board_id},\nSatellites: {info.num_sats}, Quality: {info.quality}"
            )

        if (
            "lat" in info.__dict__
            and "lon" in info.__dict__
            and time.time() - self.last_map_point_update >= 0.5
        ):
            self.last_map_point_update = time.time()
            self.point_storage.store_info(info)

    def draw_gps_data(self, points: List[Point_GPS | LineString_GPS] = None):

        total_points = len(points)
        step = 1
        low_alt = min(
            [point.alt for point in points if isinstance(point, Point_GPS)], default=0
        )
        high_alt = max(
            [point.alt for point in points if isinstance(point, Point_GPS)], default=0
        )

        for i in range(0, total_points):
            data = points[i]
            if isinstance(data, Point_GPS):
                # Map the altitude (data.alt) to a color using the GRADIENT_COLORS.
                # Adjust vmin and vmax as needed for your altitude range.
                colormap = cm.LinearColormap(
                    GRADIENT_COLORS, vmin=low_alt, vmax=high_alt
                )
                marker_color = colormap(data.alt)
                folium.CircleMarker(
                    location=[data.lat, data.lon],
                    radius=3,  # Small radius for the marker
                    color=marker_color,
                    fill=True,
                    fill_color=marker_color,
                    popup=f"Height: {data.alt}m, Timestamp: {data.time_stamp}",
                ).add_to(self.m)
            elif isinstance(data, LineString_GPS):
                points, color_idx = [], []
                for i, point in enumerate(data.points):
                    points.append([point.lat, point.lon])
                    color_idx.append(self.gradient_count)
                    # When passing a step, change the color
                    # if (i + 1) % step == 0:
                    self.gradient_count = (self.gradient_count + 1) % len(
                        GRADIENT_COLORS
                    )

                line = folium.ColorLine(
                    positions=points,
                    colors=color_idx,
                    colormap=cm.LinearColormap(
                        GRADIENT_COLORS, vmin=0, vmax=len(GRADIENT_COLORS)
                    ),
                    nb_steps=50,
                )
                line.add_to(self.m)
            else:
                print("Unhandled data type:", type(data))

    def filter_point(self, data: List[Point_GPS], board_id: str):
        return (
            [point for point in data if point.board_id == board_id]
            if board_id
            else data
        )

    def toggle_parse_state(self, state: bool):
        """Toggle the state of the real-time parser."""
        self.parse_state = state
        self.update_map()

    def change_data_source(self, data_source: str):
        if data_source == "All":
            self.source = None
        else:
            self.source = data_source

        self.refresh_map()

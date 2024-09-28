import queue
import sys
from omnibus import Receiver
from PyQt6.QtCore import pyqtSignal, QThread, QObject

from src.data_struct import Point_GPS, LineString_GPS


class RTParser(QThread, QObject):
    gps_RT_data = pyqtSignal(object)

    def __init__(self):
        QObject.__init__(self)

        self.receiver = Receiver("")
        self.running = True

    def run(self):
        self.extract_gps_data()

    def stop(self):
        self.running = False
        self.wait()

    def extract_gps_data(self):
        gps = {}
        while True:
            data = self.receiver.recv()
            msgtype = data.get("msg_type")
            
            if msgtype in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]:
                gps[msgtype] = data["data"]

            if all(key in gps for key in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]):
                timestamp = "{hrs:02}:{mins:02}:{secs:02}.{dsecs:02}".format(
                    **gps.get("GPS_TIMESTAMP", {"hrs": 0, "mins": 0, "secs": 0, "dsecs": 0}))
                latitude = gps.get("GPS_LATITUDE", {"degs": 0, "mins": 0, "dmins": 0, "direction": "N"})
                longitude = gps.get("GPS_LONGITUDE", {"degs": 0, "mins": 0, "dmins": 0, "direction": "E"})
                altitude = gps.get("GPS_ALTITUDE", {"altitude": 0, "daltitude": 0})

                # Convert latitude and longitude to decimal degrees
                lat = latitude["degs"] + latitude["mins"] / 60 + latitude["dmins"] / 3600
                if latitude["direction"] == "S":
                    lat = -lat

                lon = longitude["degs"] + longitude["mins"] / 60 + longitude["dmins"] / 3600
                if longitude["direction"] == "W":
                    lon = -lon

                # Combine altitude and decimal altitude
                he = altitude["altitude"] + altitude["daltitude"] / 100

                # Initialize Point_GPS object
                point = Point_GPS(lon=lon, lat=lat, he=he, time_stamp=timestamp)

                # Notification of new data point available
                self.gps_RT_data.emit(point)
                
                # Clear the gps dictionary for the next set of data
                gps = {}

                return point # Return the GPS_Point
            

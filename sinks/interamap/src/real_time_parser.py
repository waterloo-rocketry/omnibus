import queue
import sys
from omnibus import Receiver
from PySide6.QtCore import QThread, Signal

try:
    from src.data_struct import Point_GPS
except ImportError:
    from data_struct import Point_GPS

def parse_gps_data(gps, data):
    timestamp = "{hrs:02}:{mins:02}:{secs:02}.{dsecs:02}".format(                                
        **gps.get("GPS_TIMESTAMP", {"hrs": 0, "mins": 0, "secs": 0, "dsecs": 0}))
    latitude = gps.get("GPS_LATITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    longitude = gps.get("GPS_LONGITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    altitude = gps.get("GPS_ALTITUDE", {"altitude": 0, "daltitude": 0})
    boardId = data.get("board_id")

    # Convert latitude and longitude to decimal degrees
    lat = convert_to_decimal_degrees(latitude)
    lon = convert_to_decimal_degrees(longitude)
        
    # Combine altitude and decimal altitude
    he = altitude["altitude"] + altitude["daltitude"] / 100

    point = Point_GPS(lon=lon, lat=lat, he=he, time_stamp=timestamp, board_id=boardId)

    return point

def convert_to_decimal_degrees(coord):
    degs = coord["degs"]
    mins = coord["mins"] / 60
    dmins = coord["dmins"] / 3600
    decimal = degs + mins + dmins
    if coord.get("direction") in ["S", "W"]:
        decimal = -decimal
    return decimal

class RTParser(QThread):
    gps_RT_data = Signal(object)

    def __init__(self):
        QThread.__init__(self)

        self.receiver = Receiver("")
        self.running = False

    def run(self):
        self.running = True
        self.extract_gps_data()

    def stop(self):
        self.running = False

    def __del__(self):
        self.stop()

    def extract_gps_data(self):
        gps = {}
        while True:
            # If stop() was called
            if not self.running:
                break

            try:
                data = self.receiver.recv()
                msgtype = data.get("msg_type")
                
                if msgtype in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]:
                    gps[msgtype] = data["data"]

                if all(key in gps for key in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]):
                    point = parse_gps_data(gps, data)

                    # Notification of new data point available
                    self.gps_RT_data.emit(point)
                    
                    # Clear the gps dictionary for the next set of data
                    gps.clear()

            except queue.Empty: # Handle empty case 
                continue
            
            except Exception as e:
                print(f"Error while extracting GPS data: {e}", file=sys.stderr)
                continue  # Continue processing even if an error occurs

            
if __name__ == "__main__":
    gps = {}
    receiver = Receiver("")
    while True:
        data = receiver.recv()
        msgtype = data.get("msg_type")
        
        if msgtype in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]:
            gps[msgtype] = data["data"]

        if all(key in gps for key in ["GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]):
            print(parse_gps_data(gps, data))
            gps.clear()

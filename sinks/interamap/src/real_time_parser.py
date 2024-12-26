import queue
import sys
from omnibus import Receiver
from PySide6.QtCore import QThread, Signal

try:
    from src.data_struct import Point_GPS, Info_GPS
except ImportError:
    from data_struct import Point_GPS, Info_GPS
from enum import IntEnum

def parse_gps_data(gps, data):
    timestamp = "{hrs:02}:{mins:02}:{secs:02}.{dsecs:02}".format(                                
        **gps.get("GPS_TIMESTAMP", {"hrs": 0, "mins": 0, "secs": 0, "dsecs": 0}))
    latitude = gps.get("GPS_LATITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    longitude = gps.get("GPS_LONGITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    altitude = gps.get("GPS_ALTITUDE", {"altitude": 0, "daltitude": 0})
    num_sats = gps.get("GPS_INFO", {"num_sats": 0})["num_sats"]
    boardId = data.get("board_id")

    # Convert latitude and longitude to decimal degrees
    lat = convert_to_decimal_degrees(latitude)
    lon = convert_to_decimal_degrees(longitude)

    if boardId == "PROCESSOR":
        # If the board ID is PROCESSOR, the timestamp is not available
        timestamp = None
        lon, lat = switch_numbers_keep_sign(lon, lat) # NOTE: This is for fix a mistake in the PROCESSOR data
        
    # Combine altitude and decimal altitude
    alt = altitude["altitude"] + altitude["daltitude"] / 10000

    point = Point_GPS(lon=lon, lat=lat, alt=alt, num_sats=num_sats, time_stamp=timestamp, board_id=boardId)

    return point

def parse_gps_info(data):
    info = data.get("data",{"num_sats": 0, "quality": 0})
    num_sats = info["num_sats"]
    quality = info["quality"]
    boardId = data.get("board_id")

    info = Info_GPS(num_sats=num_sats, quality=quality, board_id=boardId)

    return info

def switch_numbers_keep_sign(a, b):
    # Swap absolute values without changing signs
    new_a = abs(b) if a >= 0 else -abs(b)
    new_b = abs(a) if b >= 0 else -abs(a)
    return new_a, new_b

def convert_to_decimal_degrees(coord):
    degs = coord["degs"]
    mins = coord["mins"] / 60
    dmins = coord["dmins"] / 600000
    decimal = degs + mins + dmins
    if coord.get("direction") in ["S", "W"]:
        decimal = -decimal
    return decimal

class BoardID(IntEnum): # Enum for board IDs (Make sure edit this if the board IDs change)
    GPS = 0
    PROCESSOR = 1

boardIds = ["GPS", "PROCESSOR"] # List of board IDs Strings

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
        gps = [{} for _ in BoardID]

        self.receiver.recv() # Clear the buffer

        while True:
            # If stop() was called
            if not self.running:
                break

            try:
                data = self.receiver.recv()
                msgtype = data.get("msg_type")
                
                if msgtype in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]:
                    if msgtype == "GPS_INFO":
                        self.gps_RT_data.emit(parse_gps_info(data))
                    board_id = data.get("board_id")
                    gps[boardIds.index(board_id)][msgtype] = data["data"]

                if all(key in gps[BoardID.GPS] for key in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]): # GPS 
                    point = parse_gps_data(gps[BoardID.GPS], data)
                    self.gps_RT_data.emit(point)
                    gps[BoardID.GPS].clear()
                    
                if all(key in gps[BoardID.PROCESSOR] for key in ["GPS_INFO", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]): # PROCESSOR (does not have GPS_TIMESTAMP)
                    point = parse_gps_data(gps[BoardID.PROCESSOR], data)
                    self.gps_RT_data.emit(point)
                    gps[BoardID.PROCESSOR].clear()

            except queue.Empty: # Handle empty case 
                continue
            
            except Exception as e:
                print(f"Error while extracting GPS data: {e}", file=sys.stderr)
                continue  # Continue processing even if an error occurs

            
if __name__ == "__main__":
    gps = [{} for _ in BoardID]
    receiver = Receiver("")
    while True:
        data = receiver.recv()
        msgtype = data.get("msg_type")
        
        if msgtype in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]:
            if msgtype == "GPS_INFO":
                print(parse_gps_info(data))
            board_id = data.get("board_id")
            gps[boardIds.index(board_id)][msgtype] = data["data"]
        
        if all(key in gps[BoardID.GPS] for key in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]): # GPS 
            print(parse_gps_data(gps[BoardID.GPS], data))
            gps[BoardID.GPS].clear()
            
        if all(key in gps[BoardID.PROCESSOR] for key in ["GPS_INFO", "GPS_LATITUDE", "GPS_LONGITUDE", "GPS_ALTITUDE"]): # PROCESSOR (does not have GPS_TIMESTAMP)
            print(parse_gps_data(gps[BoardID.PROCESSOR], data))
            gps[BoardID.PROCESSOR].clear()


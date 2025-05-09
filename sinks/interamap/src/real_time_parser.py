import queue
import sys
from omnibus import Receiver
from PySide6.QtCore import QThread, Signal

try:
    from src.data_struct import Point_GPS, Info_GPS
    from src.config import BoardID, BOARD_FIELDS
except ImportError:
    from data_struct import Point_GPS, Info_GPS
    from config import BoardID, BOARD_FIELDS # type: ignore


def parse_gps_data(gps_data, data):
    # Parse timestamp (or set to None for the processor board)
    gps_timestamp = gps_data.get("GPS_TIMESTAMP", {"hrs": 0, "mins": 0, "secs": 0, "dsecs": 0})
    timestamp = "{hrs:02}:{mins:02}:{secs:02}.{dsecs:02}".format(**gps_timestamp)

    latitude = gps_data.get("GPS_LATITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    longitude = gps_data.get("GPS_LONGITUDE", {"degs": 0, "mins": 0, "dmins": 0})
    altitude = gps_data.get("GPS_ALTITUDE", {"altitude": 0, "daltitude": 0})
    num_sats = gps_data.get("GPS_INFO", {"num_sats": -1}).get("num_sats", -1) # Default to -1 if num_sats is not available
    board_id = data.get("board_type_id")

    # Convert coordinates to decimal degrees
    lat = convert_to_decimal_degrees(latitude)
    lon = convert_to_decimal_degrees(longitude)

    if board_id == "PROCESSOR":
        # For the processor board, timestamp is not available and the coordinates need to be swapped
        timestamp = None
        lon, lat = switch_numbers_keep_sign(lon, lat)

    # Combine altitude information
    alt = altitude.get("altitude", 0) + altitude.get("daltitude", 0) / 10000

    timestamp = timestamp if timestamp is not None else "N/A"

    return Point_GPS(lon=lon, lat=lat, alt=alt, num_sats=num_sats, time_stamp=timestamp, board_id=board_id)


def parse_gps_info(data):
    info_data = data.get("data", {"num_sats": 0, "quality": 0})
    num_sats = info_data.get("num_sats", 0)
    quality = info_data.get("quality", 0)
    board_id = data.get("board_id")
    return Info_GPS(num_sats=num_sats, quality=quality, board_id=board_id)


def switch_numbers_keep_sign(a, b):
    # Swap values while keeping the sign for each number
    new_a = abs(b) if a >= 0 else -abs(b)
    new_b = abs(a) if b >= 0 else -abs(a)
    return new_a, new_b


def convert_to_decimal_degrees(coord):
    degs = coord.get("degs", 0)
    mins = coord.get("mins", 0) / 60
    dmins = coord.get("dmins", 0) / 600000
    decimal = degs + mins + dmins
    if coord.get("direction") in ["S", "W"]:
        decimal = -decimal
    return decimal


def process_gps_loop(receiver, process_func, running_checker=lambda: True):
    """
    Process incoming GPS messages from a receiver.
    
    :param receiver: Object with a recv() method returning GPS data.
    :param process_func: Function to handle parsed data (e.g. print or emit signal).
    :param running_checker: Callable that returns a boolean indicating whether to keep running.
    """
    gps = {board.value: {} for board in BoardID}

    # Clear any initial data from the buffer
    receiver.recv()

    # Combine all fields from BOARD_FIELDS into GENERAL_FIELDS
    GENERAL_FIELDS = set()
    for fields in BOARD_FIELDS.values():
        GENERAL_FIELDS.update(fields)

    print("Starting GPS data extraction loop")

    while running_checker():
        try:
            data = receiver.recv()
            msgtype = data.get("msg_type")

            if msgtype in GENERAL_FIELDS:
                board_id = data.get("board_type_id")
                # Immediately process GPS_INFO messages
                if msgtype == "GPS_INFO":
                    process_func(parse_gps_info(data))
                gps[board_id][msgtype] = data.get("data", {})

            # Check for a complete set of messages for each board
            for board, keys in BOARD_FIELDS.items():
                if all(key in gps[board] for key in keys if key != "GPS_INFO"):
                    process_func(parse_gps_data(gps[board], data))
                    gps[board].clear()

        except queue.Empty:
            continue
        except Exception as e:
            print(f"Error while extracting GPS data: {e}", file=sys.stderr)
            continue


class RTParser(QThread):
    gps_RT_data = Signal(object)

    def __init__(self):
        super().__init__()
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
        # Use process_gps_loop with a running_checker based on self.running
        process_gps_loop(self.receiver, self.gps_RT_data.emit, running_checker=lambda: self.running)


if __name__ == "__main__":
    # For testing: use process_gps_loop with print as the processing function.
    receiver = Receiver("")
    process_gps_loop(receiver, print)

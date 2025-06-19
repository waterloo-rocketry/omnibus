# Printer - Prints payload of all messages on a channel.
import sys
import datetime
from omnibus import Receiver

stdout = sys.stdout
sys.stdout = sys.stderr

receiver = Receiver("")
gps = {}

def to_decimal(message):
    if message['direction'] not in ['N', 'W']:
        raise ValueError("Wrong direction")
    return message['degs'] + (message['mins'] + message['dmins'] / 10000) / 60

def to_time(message):
    return datetime.datetime(year=2024, month=8, day=20, hour=message['hrs'], minute=message['mins'], second=message['secs']).isoformat()

def to_alt_decimal(message):
    if message['unit'] != 'M':
        raise ValueError("Wrong unit")
    return message['altitude'] + message['daltitude'] / 10000

print("type,time,lat_deg,lat_min,lat_dmin,lon_deg,lon_min,lon_dmin,alt,sats", file=stdout)

lat_dmin = 0
lon_dmin = 0

while True:
    data = receiver.recv()
    msgtype = data.get("msg_type")
    board_id = data.get("board_id")

    if board_id == "GPS" and msgtype == "GPS_TIMESTAMP":
        gps[msgtype] = data["data"]

    if board_id != "PROCESSOR":
        continue

    if msgtype in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_ALTITUDE", "GPS_LATITUDE", "GPS_LONGITUDE"]:
        gps[msgtype] = data["data"]

    if msgtype == "GPS_INFO":
        try:
            msg = "T,"
            msg += f"{to_time(gps['GPS_TIMESTAMP'])},"
            msg += f"{gps['GPS_LONGITUDE']['degs']},"
            msg += f"{gps['GPS_LONGITUDE']['mins']},"
            msg += f"{gps['GPS_LONGITUDE']['dmins']},"
            msg += f"-{gps['GPS_LATITUDE']['degs']},"
            msg += f"{gps['GPS_LATITUDE']['mins']},"
            msg += f"{gps['GPS_LATITUDE']['dmins']},"
            msg += f"{to_alt_decimal(gps['GPS_ALTITUDE'])},"
            msg += f"{gps['GPS_INFO']['num_sats']}"
            gps = {}

            print(msg, flush=True, file=stdout)
        except (KeyError, ValueError) as e:
            pass

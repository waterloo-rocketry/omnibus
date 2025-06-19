# Printer - Prints payload of all messages on a channel.
import sys
from omnibus import Receiver

stdout = sys.stdout
sys.stdout = sys.stderr

receiver = Receiver("")
gps = {}

while True:
    data = receiver.recv()
    msgtype = data.get("msg_type")
    board_id = data.get("board_id")

    if board_id != "GPS":
        continue

    if msgtype in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_ALTITUDE", "GPS_LATITUDE", "GPS_LONGITUDE"]:
        gps[msgtype] = data["data"]

    if msgtype == "GPS_ALTITUDE":
        lat = gps.get("GPS_LATITUDE")
        lon = gps.get("GPS_LONGITUDE")
        alt = gps.get("GPS_ALTITUDE")
        info = gps.get("GPS_INFO")

        if None not in [lat, lon, alt, info] and lat['degs'] != 0 and lon['degs'] != 0:
            print(f"{lat['degs'] + (lat['mins'] + lat['dmins'] / 10000) / 60:.4f}N", file=stdout, end='')
            print(f"{lon['degs'] + (lon['mins'] + lon['dmins'] / 10000) / 60:.4f}E", file=stdout, end='')
            print(f"{alt['altitude'] + alt['daltitude'] / 100:.4f}M", file=stdout, end='')
            print(f"{info['num_sats']}#", file=stdout, end='', flush=True)
        gps = {}

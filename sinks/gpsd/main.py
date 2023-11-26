# Printer - Prints payload of all messages on a channel.
import sys
from typing import Dict, Any
from omnibus import Receiver

stdout = sys.stdout
sys.stdout = sys.stderr

receiver: Receiver = Receiver("")
gps : Dict[str, Any] = {}

while True:
    data: Dict[str,Any] = receiver.recv()
    msgtype: str = data.get("msg_type")
    if msgtype in ["GPS_INFO", "GPS_TIMESTAMP", "GPS_ALTITUDE", "GPS_LATITUDE", "GPS_LONGITUDE"]:
        gps[msgtype] = data["data"]

    if msgtype == "GPS_ALTITUDE":
        msg:str = "$GPGGA,"
        msg += "{hrs:02}{mins:02}{secs:02}.{dsecs:02},".format(
            **gps.get("GPS_TIMESTAMP", {"hrs": 0, "mins": 0, "secs": 0, "dsecs": 0}))
        msg += "{degs:02}{mins:02}.{dmins:02},{direction},".format(
            **gps.get("GPS_LATITUDE", {"degs": 0, "mins": 0, "dmins": 0, "direction": "N"}))
        msg += "{degs:02}{mins:02}.{dmins:02},{direction},".format(
            **gps.get("GPS_LONGITUDE", {"degs": 0, "mins": 0, "dmins": 0, "direction": "E"}))
        msg += "{quality},{num_sats:02},1.0,".format(**
                                                     gps.get("GPS_INFO", {"quality": 0, "num_sats": 0}))
        msg += "{altitude}.{daltitude},{unit},".format(
            **gps.get("GPS_ALTITUDE", {"altitude": 0, "daltitude": 0, "unit": "M"}))
        msg += "0,M,,,"
        gps = {}

        cs: int = 0
        for c in msg[1:]:
            cs ^= ord(c)

        msg += "*{:x}".format(cs)

        print(msg, end="\r\n", flush=True, file=stdout)

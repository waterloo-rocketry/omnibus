# Printer - Prints payload of all messages on a channel.
import sys
import datetime
from omnibus import Receiver

stdout = sys.stdout
sys.stdout = sys.stderr

receiver = Receiver("")
gps = {}
last_time = 0

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

print("type,latitude,longitude", file=stdout)

while True:
    data = receiver.recv()
    msgtype = data.get("msg_type")
    board_id = data.get("board_id")

    if board_id != "GPS":
        continue

    if gps and data["data"]["time"] != last_time:
        try:
            msg = "T,"
            msg += f"{to_decimal(gps['GPS_LATITUDE'])},"
            msg += f"{-to_decimal(gps['GPS_LONGITUDE'])}"

            last_time = gps[msgtype]["time"]
            gps = {}

            print(msg, flush=True, file=stdout)
        except KeyError:
            pass

    gps[msgtype] = data["data"]

# FakeNI - Mimic the output of the NI source with dummy data for testing.

import argparse
import random
import time

import msgpack

from omnibus import Sender

from typing import cast

READ_BULK = 25  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE = 1000  # total samples/second
CHANNELS = 8  # number of analog channels to read from

parser = argparse.ArgumentParser()
parser.add_argument("--log", action="store_true", help="log the data from FakeNI")
parser.add_argument("--v3", action="store_true", help="Use message format v3")
args = parser.parse_args()
logging = args.log

sender = Sender()
CHANNEL = "DAQ/Fake"
MESSAGE_FORMAT_VERSION = 3 if args.v3 else 2

now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
log = None
if logging:
    log = open(f"log_{now}.dat", "wb")

# Hides cursor for continous print
print('\033[?25l', end="")
dots = 0
counter = 0

try:
    READ_PERIOD_v2 = int(1 / SAMPLE_RATE * 1000000000) # Up to nanosecond accuracy
    READ_PERIOD_v3 = 1 / SAMPLE_RATE
    relative_last_read_time_v2 = time.time_ns()
    relative_last_read_time_v3 = time.time()
    print(READ_PERIOD_v2 / 1000000)
    while True:
        start = time.time()
        # send a tuple of when the data was recorded and an array of the data for each channel
        if args.v3:
            relative_timestamps = [
                    relative_last_read_time_v3 + READ_PERIOD_v3 * i
                    for i in range(READ_BULK)
            ]
            ts_key = "relative_timestamps"
        else:
            relative_timestamps = list(range(
                    relative_last_read_time_v2,
                    relative_last_read_time_v2 + READ_PERIOD_v2 * READ_BULK,
                    READ_PERIOD_v2,
                ))
            ts_key = "relative_timestamps_nanoseconds"
            
        data = {
            "timestamp": start,
            "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)},
            ts_key: relative_timestamps,
            "sample_rate": SAMPLE_RATE,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }

        if args.v3:
            relative_last_read_time_v3 = relative_timestamps[-1] + READ_PERIOD_v3
        else:
            relative_last_read_time_v2 = relative_timestamps[-1] + READ_PERIOD_v2

        if log:
            log.write(msgpack.packb(data))

        # Cool continuously updating print statment
        print("\rSending", end="")
        if counter % (20*5) == 0:
            print("   ", end="")
        elif counter % 20 == 0:
            for i in range(dots):
                print(".", end="")
            if dots == 3:
                dots = 0
            else:
                dots += 1

        counter += 1

        sender.send(CHANNEL, data)
        time.sleep(max(READ_BULK/SAMPLE_RATE - (time.time() - start), 0))
finally:
    if log:
        log.close()

    # Shows cursor
    print('\033[?25h', end="")

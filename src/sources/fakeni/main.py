# FakeNI - Mimic the output of the NI source with dummy data for testing.

import argparse
import random
import time

import msgpack

from omnibus import Sender

from typing import TypedDict

READ_BULK = 25  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE = 1000  # total samples/second
CHANNELS = 8  # number of analog channels to read from

parser = argparse.ArgumentParser()
parser.add_argument("--log", action="store_true", help="log the data from FakeNI")
args = parser.parse_args()
logging = args.log

sender = Sender()
CHANNEL = "DAQ/Fake"
# Increment whenever data format changes, so incompatible tools do not attempt
# to read old logs or messages.
MESSAGE_FORMAT_VERSION = 3


class DAQ_SEND_MESSAGE_TYPE(TypedDict):
    timestamp: float
    data: dict[str, list[float]]
    relative_timestamps: list[float]
    sample_rate: int
    message_format_version: int


now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
log = None
if logging:
    log = open(f"log_{now}.dat", "wb")

# Hides cursor for continous print
print('\033[?25l', end="")
dots = 0
counter = 0

try:
    read_period_seconds = 1 / SAMPLE_RATE
    initial_host_start_time = time.time()
    total_samples_read = 0
    while True:
        start = time.time()
        relative_timestamps = [
            initial_host_start_time
            + (total_samples_read + sample_index) * read_period_seconds
            for sample_index in range(READ_BULK)
        ]
        data: DAQ_SEND_MESSAGE_TYPE = {
            "timestamp": start,
            "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)},
            "relative_timestamps": relative_timestamps,
            "sample_rate": SAMPLE_RATE,
            "message_format_version": MESSAGE_FORMAT_VERSION,
        }

        total_samples_read += READ_BULK

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

# FakeNI - Mimic the output of the NI source with dummy data for testing.

import argparse
import random
import time

import msgpack

from omnibus import Sender
from typing import Dict, Optional, IO, Any

READ_BULK: int = 200  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE: int = 10000  # total samples/second
CHANNELS: int = 8  # number of analog channels to read from

parser: argparse.ArgumentParser = argparse.ArgumentParser()
parser.add_argument("--log", action="store_true", help="log the data from FakeNI")
logging: bool = parser.parse_args().log

sender: Sender = Sender()
CHANNEL: str = "DAQ/Fake"

now: str = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08

log: Optional[IO[bytes]] = None
if logging:
    log = open(f"log_{now}.dat", "wb")

# Hides cursor for continous print
print('\033[?25l', end="")
dots: int = 0
counter: int = 0

try:
    while True:
        start: float = time.time()
        # send a tuple of when the data was recorded and an array of the data for each channel
        data: Dict[str, Any] = {
            "timestamp": start,
            "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)}
        }

        if logging and log is not None:
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
    if logging and log is not None:
        log.close()

    # Shows cursor
    print('\033[?25h', end="")


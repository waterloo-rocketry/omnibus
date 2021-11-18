# FakeNI - Mimic the output of the NI source with dummy data for testing.

import random
import time

import msgpack

from omnibus import Sender

READ_BULK = 200  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE = 10000  # total samples/second
CHANNELS = 8  # number of analog channels to read from

sender = Sender()
CHANNEL = "DAQ/Fake"

now = time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime())  # 2021-07-12_22-35-08
with open(f"log_{now}.dat", "wb") as log:
    while True:
        start = time.time()
        # send a tuple of when the data was recorded and an array of the data for each channel
        data = {
            "timestamp": start,
            "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)}
        }

        log.write(msgpack.packb(data))
        sender.send(CHANNEL, data)
        time.sleep(max(READ_BULK/SAMPLE_RATE - (time.time() - start), 0))

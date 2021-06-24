# FakeNI - Mimic the output of the NI source with dummy data for testing.
import random
import time
from omnibus import Sender
READ_BULK = 200  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE = 20000  # total samples/second
CHANNELS = 8  # number of analog channels to read from
SERVER = "tcp://localhost:5075"

sender = Sender(SERVER, "NI/Fake")

while True:
    start = time.time()
    # send a tuple of when the data was recorded and an array of the data for each channel
    data = {
        "timestamp": start,
        "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)}
    }
    sender.send(data)
    time.sleep(max(READ_BULK/SAMPLE_RATE - (time.time() - start), 0))
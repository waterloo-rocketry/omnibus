# FakeNI - Mimic the output of the NI source with dummy data for testing.
import random
import time
from omnibus import Sender, Message

READ_BULK = 200  # mimic how the real NI box samples in bulk for better performance
SAMPLE_RATE = 20000  # total samples/second
CHANNELS = 8  # number of analog channels to read from
CHANNEL_NAMES = [f"DAQ/Fake{i}" for i in range(CHANNELS)] # analog channels to read from

sender = Sender("")

while True:
    start = time.time()
    for channel in CHANNEL_NAMES:
        # send a tuple of when the data was recorded and an array of the data
        payload = (start, [random.random() for _ in range(READ_BULK)])
        sender.send_message(Message(channel, time.time(), payload))
    time.sleep(max(READ_BULK/SAMPLE_RATE - (time.time() - start), 0))
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

logging = True if input("Log FakeNI data? (y/N): ").upper() == "Y" else False
if (logging):
    log = open(f"log_{now}.dat", "wb")

# Hides cursor for continous print
print('\033[?25l', end="")
dots = 0
counter = 0

try:
    while True:
        start = time.time()
        # send a tuple of when the data was recorded and an array of the data for each channel
        data = {
            "timestamp": start,
            "data": {f"Fake{i}": [random.random() for _ in range(READ_BULK)] for i in range(CHANNELS)}
        }

        if (logging):
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
except KeyboardInterrupt:
    if logging:
        log.close()

    #Shows cursor
    print('\033[?25h', end="")

import time
import sys
import msgpack
import random
import zmq

SERVER_URL = "tcp://localhost:5559"
SAMPLE_RATE = 10000 # Samples/sec.
READ_BULK = 200 # Read multiple samples at once for increased performance.

context = zmq.Context()
sender = context.socket(zmq.PUB)
sender.connect(SERVER_URL)

print("Connected to 0MQ server.")

while True:
	start = time.time()
	data = (time.time(), [[random.randint(-10,10) for _ in range(READ_BULK)] for _ in range(16)])
	sender.send(msgpack.packb(data)) # Use pickle to seralize the data because I'm lazy
	time.sleep(max(READ_BULK/SAMPLE_RATE - (time.time() - start), 0))

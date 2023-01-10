# Send stdout from one program over omnibus 

import msgpack
import json

from omnibus import Sender

sender = Sender()
CHANNEL = "SE/Fake"

while True:
	sender.send(CHANNEL, json.loads(input()))
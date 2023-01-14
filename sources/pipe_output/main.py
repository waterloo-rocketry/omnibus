from subprocess import Popen, PIPE
import sys
import time
from omnibus import Sender
import json

inp = Popen(sys.argv[1:], stdout = PIPE)
sender = Sender()
CHANNEL = "SE/Fake"

for line in inp.stdout:
	js = json.loads(line.strip())
	sender.send(CHANNEL, js)
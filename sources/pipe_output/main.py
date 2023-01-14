import json
from subprocess import Popen, PIPE
import sys

from omnibus import Sender


inp = Popen(sys.argv[1:], stdout=PIPE)
sender = Sender()
CHANNEL = "SE/Fake"

for line in inp.stdout:
    data = json.loads(line.strip())
    sender.send(CHANNEL, data)

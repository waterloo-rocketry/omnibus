import json
from subprocess import Popen, PIPE
import sys

from omnibus import Sender


inp = Popen(sys.argv[1:], stdout=PIPE)
sender = Sender()
CHANNEL = "SE/Fake"

stream = inp.stdout
if stream is None:
    raise RuntimeError("subprocess was created without a stdout pipe")

for line in stream:
    data = json.loads(line.strip())
    sender.send(CHANNEL, data)

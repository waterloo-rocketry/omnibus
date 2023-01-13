from subprocess import Popen, PIPE
import sys
import time

inp = Popen(['python', 'test.py'], stdout = PIPE)
proc1 = Popen(['python', 'sender.py'], stdin=PIPE)

for line in inp.stdout:
	proc1.stdin.write(line)

proc1.wait()
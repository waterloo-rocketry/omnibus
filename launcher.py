from subprocess import Popen
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument('--test', action='store_true', help="run omnibus with FakeNI source")
test = parser.parse_args().test

profiles = {
    "test": [
        ['python', '-m', 'omnibus'],
        ['python', 'sources/fakeni/main.py'],
        ['python', 'sinks/dashboard/main.py']
    ],
    "real": [
        ['python', '-m', 'omnibus'],
        ['python', 'sources/fakeni/main.py'],
        ['python', 'sinks/dashboard/main.py']
    ]
}

if test:
    profile = profiles["test"]
else:
    profile = profiles["real"]

p = []

for i in range(len(profile)):
    p.append(Popen(profile[i]))
    time.sleep(0.2)

while p[len(p)-1].poll() == None:
    continue

for i in range(len(p)):
    p[len(p)-1-i].terminate()

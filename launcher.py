from subprocess import Popen, PIPE
from sys import platform
from os import kill 
import time, signal

if platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP


# Profiles for what parts of Omnibus should be run
# Files inside each profile should be listed 
# IN ORDER of how they should be run 
profiles = {
    "Test": [
        ['python', '-m', 'omnibus'],
        ['python', 'sources/fakeni/main.py'],
        ['python', 'sinks/dashboard/main.py']
    ],
    "DAQ": [
        ['python', '-m', 'omnibus'],
        ['python', 'sources/ni/main.py'],
    ],
    "Dashboard": [
        ['python', 'sinks/dashboard/main.py']
    ],
    "Log + Dashboard": [
        ['python', 'sinks/globallog/main.py'],
        ['python', 'sinks/dashboard/main.py']
    ]
    # Add new profiles here
}

# Presents the user with a list of all available 
# profiles and prompts them to choose one
print("The following profiles are available to run Omnibus:\n")

for i, profile in enumerate(profiles):
    print(f"\t{i+1}. {profile}")
print()

# Keep asking for input if invalid entry is given
selection = 0
while selection < 1 or selection > i+1:
    selection = input(f"Please enter the number corresponding to your choice [1-{i+1}]: ")
    try:
        selection = int(selection)
    except ValueError:
        selection = 0

profile = profiles[list(profiles)[selection-1]]
p = []
print(f"Running Omnibus with selection {selection}...")

# Run every file in the background
for i in range(len(profile)):
    # This distinction is necessary to properly 
    # exit the subprocesses on Windows
    if platform == "win32":
        process = Popen(profile[i], stdout=PIPE, stderr=PIPE, creationflags=CREATE_NEW_PROCESS_GROUP)
    else:
        process = Popen(profile[i], stdout=PIPE, stderr=PIPE)

    p.append(process)

    # Time delay cause CPU too fast and Omnibus 
    # needs time to setup communication channels
    time.sleep(0.5)

class Finished(Exception):
    pass

# If any file exits or the user presses control + c
# terminate all other files that are running
try:
    while True:
        for process in p:
            if process.poll() != None:
                raise Finished
except (Finished, KeyboardInterrupt, Exception):
    for i in p:
        if platform == "win32":
            kill(i.pid, signal.CTRL_C_EVENT)
        else:
            i.send_signal(signal.SIGINT)

        print(f"\nOutput from {i.args}:\n{i.stdout.read().decode()}")

        if i.returncode not in [None, 0]:
            print(i.stderr.read().decode())

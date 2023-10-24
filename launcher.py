import os
import signal
import subprocess
import sys
import time

# Some specific commands are needed for Windows vs macOS/Linux
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP
    python_executable = "venv/Scripts/python"
else:
    python_executable = "python"

# Parse folders for sources and sinks
modules = {"sources" : os.listdir('sources'), "sinks" : os.listdir('sinks')}

# Remove dot files
for module in modules.keys():
    for item in modules[module]:
        if item.startswith("."):
            modules[module].remove(item)

for module in modules.keys():
    print(f"{module.capitalize()}:")
    for i, item in enumerate(modules[module]):
        print(f"\t{i+1}. {item.capitalize()}")

# Construct CLI commands to start Omnibus
source_selection = input(f"\nPlease enter your Source choice [1-{len(modules['sources'])}]: ")
sink_selection = input(f"Please enter your Sink choice [1-{len(modules['sinks'])}]: ")
omnibus = [python_executable, "-m", "omnibus"]
source = [python_executable, f"sources/{modules['sources'][int(source_selection) - 1]}/main.py"]
sink = [python_executable, f"sinks/{modules['sinks'][int(sink_selection) - 1]}/main.py"]

commands = [omnibus, source, sink]
processes = []
print("Launching... ", end="")

# Execute commands as subprocesses
for command in commands:
    if sys.platform == "win32":
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   creationflags=CREATE_NEW_PROCESS_GROUP)
    else:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    time.sleep(0.5)
    processes.append(process)

print("Done!")

# Blank exception just for processes to throw
class Finished(Exception):
    pass

# If any file exits or the user presses control + c,
# terminate all other files that are running
try:
    while True:
        for process in processes:
            if process.poll() != None:
                raise Finished
except (Finished, KeyboardInterrupt, Exception):
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)

        # Dump output and error (if exists) from every
        # process to the shell 
        output, err = process.communicate()
        output, err = output.decode(), err.decode()
        print(f"\nOutput from {process.args}:")
        print(output)

        if err and "KeyboardInterrupt" not in err:
            print(f"\nError from {process.args}:")
            print(err)
finally:
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)

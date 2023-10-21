import os
import signal
import subprocess
import sys
import time
import logging
from logtool import init_loggers

# Some specific commands are needed for Windows vs macOS/Linux
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP

# Parse folders for sources and sinks
modules = {"sources" : os.listdir('sources'), "sinks" : os.listdir('sinks')}

for module in modules.keys():
    print(f"{module.capitalize()}:")
    for i, item in enumerate(modules[module]):
        print(f"\t{i+1}. {item.capitalize()}")

# Construct CLI commands to start Omnibus
omnibus = ["python", "-m", "omnibus"]
source_selection = input(f"\nPlease enter your Source choice [1-{len(modules['sources'])}]: ")
sink_selection = input(f"Please enter your Sink choice [1-{len(modules['sinks'])}]: ")
source = ["python", f"sources/{modules['sources'][int(source_selection) - 1]}/main.py"]
sink = ["python", f"sinks/{modules['sinks'][int(sink_selection) - 1]}/main.py"]

loggers = init_loggers()
print("Loggers Initiated")

commands = [omnibus, source, sink]
processes = []
print("Launching... ", end="")

# Execute commands as subprocesses
for command in commands:
    if sys.platform == "win32":
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                   creationflags=CREATE_NEW_PROCESS_GROUP)
        time.sleep(0.5)
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
            os.kill(process.pid, signal.CTRL_C_EVENT)
        else:
            process.send_signal(signal.SIGINT)

        # Dump output and error (if exists) from every
        # process to the coresponding log file
        output, err = process.communicate()
        output, err = output.decode(), err.decode()
        try:          
            loggers[process.args[-1].split("/")[1]].info(f"From {process.args}:{output}")
            print(f"\nOutput from {process.args} logged")  
        except IndexError:
            print(f"\nOutput from {process.args} logged in misc.log")
            loggers["misc"].info(f"From{process.args}:{output}")

        if err and "KeyboardInterrupt" not in err:
            try:
                loggers[process.args[-1].split("/")[1]].error(f"From {process.args}:{err}")
                print(f"\nError from {process.args} logged")
            except IndexError:
                print(f"\nError from {process.args} logged in misc.log")
                loggers["misc"].error(f"From{process.args}:{err}")
    logging.shutdown()
finally:
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_C_EVENT)
        else:
            process.send_signal(signal.SIGINT)
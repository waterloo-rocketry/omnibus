import os
import signal
import subprocess
import sys
import time
import logging
from logtool import Logger


# Some specific commands are needed for Windows vs macOS/Linux
if sys.platform == "win32":
    from subprocess import CREATE_NEW_PROCESS_GROUP
    python_executable = "venv/Scripts/python"
else:
    python_executable = "python"

# Parse folders for sources and sinks
modules = {"sources": os.listdir('sources'), "sinks": os.listdir('sinks')}

# Remove dot files
for module in modules.keys():
    for item in modules[module]:
        if item.startswith("."):
            modules[module].remove(item)

for module in modules.keys():
    print(f"{module.capitalize()}:")
    for i, item in enumerate(modules[module]):
        print(f"\t{i+1}. {item.capitalize()}")

#arrays to store the user selection 
srcSelected=[]
sinkSelected=[]

# Construct CLI commands to start Omnibus
source_selection = input(f"\nPlease enter your Source choice [1-{len(modules['sources'])}]: ")
sink_selection = input(f"Please enter your Sink choice [1-{len(modules['sinks'])}]: ")

#process the source/sink_selection to see how many were selected 
sources=source_selection.split()
srcSelected=[int(item) for item in sources]
print(srcSelected)

sinks=sink_selection.split()
sinkSelected=[int(item) for item in sinks]
print(sinkSelected)

commands=[]
logger = Logger() # Create loggers -need to change this to allow multiple sources/sinks 
omnibus = [python_executable, "-m", "omnibus"]
commands.append(omnibus)

if srcSelected:
    for selection in srcSelected:
        source=[python_executable, f"sources/{modules['sources'][selection - 1]}/main.py"]
        logger.add_logger(f"sources/{modules['sources'][selection - 1]}")
        commands.append(source)

if sinkSelected:
    for selection in sinkSelected:
        sink = [python_executable, f"sinks/{modules['sinks'][int(selection) - 1]}/main.py"]
        logger.add_logger(f"sinks/{modules['sinks'][selection - 1]}")
        commands.append(sink)


print("Loggers Initiated")

processes = []
print("Launching... ", end="")

# Execute commands as subprocesses

for command in commands:
    print("how many times does it come in here")
    #run the remaining processes 
    #subprocess.Popen(command)
    if sys.platform == "win32":
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=CREATE_NEW_PROCESS_GROUP)
    else:
        process=subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE ) 
    time.sleep(0.5)
    processes.append(process)

print("Done!")
print (processes)
# Blank exception just for processes to throw
class Finished(Exception):
    pass

# If any file exits or the user presses control + c,
# terminate all other files that are running
try:
    while True:
        for process in processes:
            if process.poll() != None:
                print("process: ", process)
                raise Finished
except (Finished, KeyboardInterrupt, Exception):
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)

        # Dump output and error (if exists) from every
        # process to the coresponding log file
        output, err = process.communicate()
        output, err = output.decode(), err.decode()
        
        # Log outputs
        logger.log_output(process, output)

        # Log errors
        if err and "KeyboardInterrupt" not in err:
            logger.log_error(process, err)
            
    logging.shutdown()
finally:
    for process in processes:
        if sys.platform == "win32":
            os.kill(process.pid, signal.CTRL_BREAK_EVENT)
        else:
            process.send_signal(signal.SIGINT)  


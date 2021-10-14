import sys
from subprocess import Popen, CREATE_NEW_CONSOLE


profiles = {
    "test": ['python -m omnibus',
             'python sinks/plot/main.py',
             'python sources/fakeni/main.py'],
    "texas": ['python sources/parsley/main.py',
              'python sources/ni/main.py',
              'python -m omnibus']
}


try:
    selection = sys.argv[1]
    processes = profiles[selection]
except (KeyError, IndexError):
    print('Please enter a single valid profile selection (ex. python launcher.py texas)')


for process in processes:
    Popen(process, creationflags=CREATE_NEW_CONSOLE)

import sys
from subprocess import Popen, CREATE_NEW_CONSOLE


profiles = {  # Note: enter each command as a string enclosed with double quotations
    "test": ['"python -m omnibus"',
             '"python sinks/plot/main.py"',
             '"python sources/fakeni/main.py"'],
    "texas": ['"python sources/parsley/main.py"',
              '"python sources/ni/main.py"',
              '"python -m omnibus"']
}


try:
    if(sys.argv[1] == "_wrap"):

        p = Popen(sys.argv[2])
        p.wait()
        print('...')
        x = input('Press enter to quit')

    else:
        selection = sys.argv[1]
        processes = profiles[selection]
        for script in processes:
            Popen(f'python launcher.py _wrap {script}', creationflags=CREATE_NEW_CONSOLE)

except (KeyError, IndexError):
    print('Please enter a single valid profile selection (ex. python launcher.py texas)')

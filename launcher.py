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


def run():  # runs processes in seperate consoles
    for process in processes:
        Popen(process, creationflags=CREATE_NEW_CONSOLE)


def test():  # function that runs all processes in a single console, so error messages get displayed
    for process in processes:
        Popen(process)


try:
    if(sys.argv[1] == "_test"):
        selection = sys.argv[2]
        processes = profiles[selection]
        test()
    else:
        selection = sys.argv[1]
        processes = profiles[selection]
        run()

except (KeyError, IndexError):
    print('Please enter a single valid profile selection (ex. python launcher.py texas)')
    print('''If you wish to launch the profile all in a singel console to check for errors, 
    enter "_test" followed by the profile selection (ex. python launcher.py _test texas)''')

import sys
from subprocess import Popen, CREATE_NEW_CONSOLE


profiles = {
    "test": ['python -m omnibus',
             'python sinks/plot/main.py',
             'python sources/fakeni/main.py'],
    "texas": ['python sources/parsley/main.py $arg',
              'python sources/ni/main.py',
              'python -m omnibus']
    #   Add other profiles in here
    #   If any commands require arguments to be passed in, write $arg in its place

}


try:
    if sys.argv[1] == "_wrap":
        p = Popen(sys.argv[2])
        if p.wait() != 0:
            input('Press enter to quit')

    else:
        selection = sys.argv[1]
        processes = profiles[selection]
        args = sys.argv[2:]

        for process in processes:
            while '$arg' in process:
                process = process.replace('$arg', args[0], 1)
                args.pop(0)
            Popen(f'python launcher.py _wrap "{process}"', creationflags=CREATE_NEW_CONSOLE)

except (KeyError, IndexError):
    print('Please enter a single valid profile selection (ex. python launcher.py texas)')
    print('Ensure that you have entered the correct amount of args required for each script in the right order')

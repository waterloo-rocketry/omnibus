from subprocess import Popen
import platform

# Set the correst source based on whether or not the user is testing Omnibus
test = ''
while test != 'y' and test != 'n':
    test = input("Is this a test of Omnibus? [y/n] ").lower()

if (test == 'y'):
    source = 'fakeni'
else:
    source = 'ni'

# Darwin is macOS, Windows is Windows, Linux... maybe later
if platform.system() == "Darwin":
    import os
    import time

    # Get the current directory (where omnibus is located)
    omnibus_path = os.getcwd()

    # Change this to if you named your virtual environment something else
    venv_name = 'venv'

    # Change this if you want to use a different terminal on mac
    terminal = 'terminal'

    # Writes correct paths to scripts
    with open("omnibus.sh", 'w') as f:
        f.write(f'cd {omnibus_path}\nsource {venv_name}/bin/activate\npython -m omnibus\ntrap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT')

    with open("source.sh", 'w') as f:
        f.write(f'cd {omnibus_path}\nsource {venv_name}/bin/activate\npython sources/{source}/main.py\ntrap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT')

    with open("dashboard.sh", 'w') as f:
        f.write(f'cd {omnibus_path}\nsource {venv_name}/bin/activate\npython sinks/dashboard/main.py\ntrap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT')

    # Open new terminal windows and run the scripts that run python commands
    Popen(['open', '-a', terminal, 'omnibus.sh']).communicate()
    Popen(['open', '-a', terminal, 'source.sh']).communicate()
    
    # Dashboard needs to be delayed slightly so omnibus and sink can find each other
    time.sleep(0.5)
    Popen(['open', '-a', terminal, 'dashboard.sh']).communicate()

elif platform.system() == "Windows":
    # NOT TESTED YET - need someone with a Windows machine
    from subprocess import CREATE_NEW_CONSOLE

    commands = ['python -m omnibus',
                f'python sources/{source}/main.py',
                'python sinks/dashboard/main.py']

    for command in commands:
        Popen(command, creationflags=CREATE_NEW_CONSOLE)

else:
    print("Sorry, your operating system can't be automatically detected")
    print("Please start Omnibus manually")

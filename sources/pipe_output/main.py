import subprocess
import sys

subprocess.run([sys.argv[1], '|', 'python', 'sender.py'])
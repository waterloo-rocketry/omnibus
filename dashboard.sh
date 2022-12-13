cd /Users/ozayrraazi/Documents/Rocketry/omnibus
source venv/bin/activate
python sinks/dashboard/main.py
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
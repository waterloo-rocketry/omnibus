cd /Users/ozayrraazi/Documents/Rocketry/omnibus
source venv/bin/activate
python sources/fakeni/main.py
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
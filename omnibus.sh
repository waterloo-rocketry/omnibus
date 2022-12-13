cd /Users/ozayrraazi/Documents/Rocketry/omnibus
source venv/bin/activate
python -m omnibus
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT
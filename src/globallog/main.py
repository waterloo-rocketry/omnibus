# Global logger - Saves messages passed through bus to asc-time.log
import argparse
import signal
import sys
import time
from datetime import datetime

import msgpack

from omnibus import Receiver

# Will log all messages passing through bus
CHANNEL = ""

# Controls whether logged timestamps use producer time or local time
parser=argparse.ArgumentParser(description="Omnibus Global Logger")
parser.add_argument(
    "-l",
    "--local-timestamps",
    action="store_true",
    help="Use receiver (local) timestamps instead of producer timestamps",
)
args = parser.parse_args()
USE_LOCAL_TIMESTAMPS = args.local_timestamps
print("USE_LOCAL_TIMESTAMPS =", USE_LOCAL_TIMESTAMPS) # Test for flag

# Retrieves current date and time
CURTIME = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")

# Creates filename
fname = CURTIME + ".log"
# We use a shorter reconnect attempt here because globallog should be
# receiving a lot of messages anyways and data integrity is a lot more important
# Even if the reset does affect a few messages, some data is better than no data.
receiver = Receiver(CHANNEL, seconds_until_reconnect_attempt=2)

dots = 0
counter = 0
exit_program = False  # Exit flag


# Define a handler for graceful exit
def graceful_exit(signum, frame):
    global exit_program
    print("\nSignal received (SIGINT), exiting gracefully...")
    exit_program = True


# Set up signal handlers for SIGINT (Ctrl + C) and SIGTERM
signal.signal(signal.SIGINT, graceful_exit)  # Handles Ctrl + C
signal.signal(signal.SIGTERM, graceful_exit)  # Handles termination signal

# Creates new file
with open(fname, "wb") as f:
    print(f"Data will be logged to {fname}")
    # Hides cursor for continous print
    print("\033[?25l", end="")

    try:
        while not exit_program:
            # Cool continuously updating print statment
            print("\rLogging... (Press Ctrl + C to stop)", end="")

            if counter % (20 * 5) == 0:
                print("   ", end="")
            elif counter % 20 == 0:
                for i in range(dots):
                    print(".", end="")
                if dots == 3:
                    dots = 0
                else:
                    dots += 1

            counter += 1

            # Try receiving message with timeout (if possible) to avoid blocking
            msg = receiver.recv_message(timeout=10)  # 10 ms timeout
            if msg:
                timestamp = (
                    time.time() 
                    if USE_LOCAL_TIMESTAMPS
                    else msg.timestamp
                )
                
                f.write(msgpack.packb([msg.channel, timestamp, msg.payload]))

    finally:
        f.close()
        # Shows cursor
        print("\033[?25h", end="")
        print("Program has exited gracefully.")
        print(f"Data has been logged to {fname}")
        sys.exit(0)  # Exit the program

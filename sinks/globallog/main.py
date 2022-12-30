# Global logger - Saves messages passed through bus to asc-time.log

from datetime import datetime

import msgpack

from omnibus import Receiver

# Will log all messages passing through bus
CHANNEL = ""
# Retrieves current date and time
CURTIME = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
# Creates filename
fname = CURTIME + ".log"
receiver = Receiver(CHANNEL)

dots = 0
counter = 0

# Creates new file
with open(fname, "wb") as f:
    print(f"Data will be logged to {fname}")
    # Hides cursor for continous print
    print('\033[?25l', end="")

    try:
        while True:
            # Cool continuously updating print statment
            print("\rLogging", end="")
            if counter % (20*5) == 0:
                print("   ", end="")
            elif counter % 20 == 0:
                for i in range(dots):
                    print(".", end="")
                if dots == 3:
                    dots = 0
                else:
                    dots += 1

            counter += 1

            # Receives message and writes it to file
            msg = receiver.recv_message()
            f.write(msgpack.packb([msg.channel, msg.timestamp, msg.payload]))
    finally:
        # Shows cursor
        print('\033[?25h', end="")

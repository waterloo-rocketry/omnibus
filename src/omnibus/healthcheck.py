# This Python script performs health checks
# on Omnibus Server by sending a healthcheck
# message pack and check if it receives the same
# message from Omnibus Server.
#
# Note that this script is intended to be run
# by the Docker healthcheck mechanism.
# Therefore, it exits with code 0 on success
# and code 1 on failure, and does not
# produce any output nor loop indefinitely.

import random
import sys
import time

from omnibus import Sender, Receiver

# Setup sender to send HEALTHCHECK message.
sender = Sender()
CHANNEL = "HEALTHCHECK"

# Only listen to HEALTHCHECK channel.
receiver = Receiver("HEALTHCHECK")


def send_healthcheck():
    # Send alive message first to ensure connection is established.
    while receiver.recv(1) is None:
        sender.send(CHANNEL, "_ALIVE")

    start = time.time()
    random_number = random.randint(0, sys.maxsize)

    # Prepare healthcheck data.
    data = {
        "timestamp": start,
        "healthcheck_id": random_number,
    }

    sender.send(CHANNEL, data)

    return data


def receive_healthcheck(expected_data, timeout=5):
    data = receiver.recv(timeout=timeout)

    if data is None:
        return False

    return data == expected_data


if __name__ == "__main__":
    expected_data = send_healthcheck()
    if receive_healthcheck(expected_data):
        sys.exit(0)
    else:
        sys.exit(1)

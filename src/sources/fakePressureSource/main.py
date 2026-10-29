"""Publish a fake DAQ pressure reading, for bench-testing without a real pressure feed.
Type a number and press enter to change the pressure (PSI)."""
import argparse
import threading
import time

from omnibus import Sender

CHANNEL = "DAQ/FakePressure"
PUBLISH_INTERVAL_S = 0.1
READ_BULK = 25
SAMPLE_RATE = round(READ_BULK / PUBLISH_INTERVAL_S)
MESSAGE_FORMAT_VERSION = 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('psi', nargs='?', type=float, default=0.0,
                        help="Starting pressure (PSI). Default: %(default)s")
    parser.add_argument('--pt-name', default="Fake0",
                        help="The PT name to publish under. Must match the auto-sequence's "
                        "AUTO_SEQUENCE_PT_NAME. Default: %(default)s")
    args = parser.parse_args()

    sender = Sender()
    pt_name = args.pt_name
    psi = args.psi

    def publish_forever():
        while True:
            now = time.time()
            sender.send(CHANNEL, {
                "timestamp": now,
                "data": {pt_name: [psi] * READ_BULK},
                "relative_timestamps": [now + i / SAMPLE_RATE for i in range(READ_BULK)],
                "sample_rate": SAMPLE_RATE,
                "message_format_version": MESSAGE_FORMAT_VERSION,
            })
            time.sleep(PUBLISH_INTERVAL_S)

    threading.Thread(target=publish_forever, daemon=True).start()
    print(f"Publishing '{pt_name}' on {CHANNEL}.")

    while True:
        print(f"Pressure: {psi} PSI. New value: ", end="", flush=True)
        line = input().strip()
        try:
            psi = float(line)
        except ValueError:
            print(f"Not a number: {line!r}")


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        pass

import time

import serial

from omnibus import Sender

import autosequence
import rlcs
import commander
from cli import parse_args
from pressure_feed import PressureFeed


def reader(serial_port: serial.Serial | None):
    if serial_port is None:
        return input

    def _reader():
        while True:
            c = serial_port.read()
            if c != b'W':
                continue

            output = b'W' + serial_port.read(rlcs.EXPECTED_SIZE - 1)

            if output[-1] != ord('R'):
                print(f"Incorrectly terminated RLCS message: {[c for c in output]}")
                continue

            return output

    return _reader


def main():
    args = parse_args()

    serial_port = None if args.port == "-" else serial.Serial(args.port, 115200)
    readline = reader(serial_port)

    sender: Sender | None = None
    CHANNEL = "RLCS"

    if not args.solo:
        sender = Sender()

    sequencer = None
    pressure_feed = None
    if args.auto_sequence:
        autosequence.require_operator_confirmation(
            autosequence.AUTO_SEQUENCE_PT_NAME,
            autosequence.AUTO_SEQUENCE_TARGET_PRESSURE_VALUE,
            args.auto_sequence_time_ms)
        pressure_feed = PressureFeed(autosequence.AUTO_SEQUENCE_PT_NAME)
        pressure_feed.start()
        sequencer = autosequence.AutoSequencer(time_to_fire_ms=args.auto_sequence_time_ms)

    try:
        while True:
            line = readline()

            if not len(line):
                continue

            parsed_data = rlcs.parse_rlcs(line)

            if not parsed_data:
                continue

            commander.command(parsed_data)

            # Each RLCS frame doubles as the heartbeat that keeps the firmware override alive.
            if sequencer and pressure_feed and serial_port:
                should_open_qd301 = sequencer.update(
                    time.monotonic(),
                    armed=parsed_data["Towerside Armed"] == "TRUE",
                    ignition_held=parsed_data["Ignition Primary Command"] == "OPEN",
                    pressure=pressure_feed.latest,
                    qd301_reported_open=parsed_data["QD301 Command"] == "OPEN")
                if should_open_qd301:
                    serial_port.write(rlcs.QD301_OVERRIDE_OPEN)

            if not args.solo and sender is not None:  # if connect to omnibus
                sender.send(CHANNEL, parsed_data)

            rlcs.print_data(parsed_data)
    finally:
        if sequencer and serial_port:
            serial_port.write(rlcs.QD301_OVERRIDE_RELEASE)
            print("[AUTO-SEQUENCE] Exiting: released QD301 override.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

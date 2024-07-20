import argparse
import serial

from omnibus import Sender

import rlcs
import commander


def reader(port: str):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)  # listen on the RLCS port

    def _reader():
        while True:
            c = s.read()
            if c != b'W':
                continue

            output = b'W' + s.read(rlcs.EXPECTED_SIZE - 1)

            if output[-1] != ord('R'):
                print(f"Incorrectly terminated RLCS message: {[c for c in output]}")
                continue

            return output

    return _reader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--solo', action='store_true',
                         help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    readline = reader(args.port)

    if not args.solo:
        sender = Sender()
        CHANNEL = "RLCS"

    while True:
        line = readline()

        if not len(line):
            continue

        parsed_data = rlcs.parse_rlcs(line)

        if not parsed_data:
            continue

        commander.command(parsed_data)

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

        rlcs.print_data(parsed_data) 



if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

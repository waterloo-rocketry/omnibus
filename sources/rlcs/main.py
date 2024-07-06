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
        return s.readline().strip(b'\r\n')
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

    line = b''

    while True:
        old_len = len(line)
        line += readline()

        if old_len == len(line):
            continue

        parsed_data = rlcs.parse_rlcs(line)

        if not parsed_data:
            if int(line[-1]) == ord('R'):
                line = b''
            else:
                line += b'\n'
            continue

        line = b''

        commander.command(parsed_data)

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

        rlcs.print_data(parsed_data)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

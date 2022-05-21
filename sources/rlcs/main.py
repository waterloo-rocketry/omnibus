import argparse
import serial

from omnibus import Sender

import rlcs.rlcs as rlcs


def reader(port):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)  # listen on the RLCS port

    def _reader():
        return s.readline().strip(b'\r\n').decode('utf-8')
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
        CHANNEL = "CAN/RLCS"

    while True:
        line = readline()

        if not line:
            break

        parsed_data = rlcs.parse_rlcs(line)

        if not parsed_data:
            continue

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

        print(rlcs.fmt_line(parsed_data))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

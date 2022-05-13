import argparse
import serial

from omnibus import Sender

import rlcs


def reader(port):
    if port == "-":
        return input
    s = serial.Serial(port, 115200) # listen on the RLCS port

    def _reader():
        return s.readline().strip(b'\r\n').decode('utf-8')
    return _reader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--format', default='usb',
                        help='Options: logger, usb. Parse input in RocketCAN Logger or USB format')
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

        # check if line is in a valid input format
        if line[0] != "W" or line[len(line)-1] != "R":
            print("Data " + line + " is invalid (must end with R and begin with W")
            continue

        if len(line) != 34:
            print("Warning: Format {} is wrong. Expected 34 characters, got {}".format(line, len(line)))
            continue  # In the future, we may want to extract information from the message despite poor formatting

        stripped_data = line[1:len(line)-1]
        parsed_data = rlcs.parse_rlcs(stripped_data)

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)
        else:  # print debug code to console
            print(rlcs.fmt_line(parsed_data))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

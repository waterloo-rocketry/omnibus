import argparse
import serial

from omnibus import Sender
import parsley


def reader(port):
    if port == "-":
        return input
    s = serial.Serial(port, 9600)

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
    parser = parsley.parse_logger if args.format == 'logger' else parsley.parse_usb_debug
    if not args.solo:
        sender = Sender()
        CHANNEL = "CAN/Parsley"

    while True:
        line = readline()
        if not line:
            break

        # treat repeated messages in the same way as USB debug
        if line.strip() == '.':
            print('.')
            continue

        msg_sid, msg_data = parser(line)
        parsed_data = parsley.parse(msg_sid, msg_data)

        print(parsley.fmt_line(parsed_data))
        if not args.solo:
            sender.send(CHANNEL, parsed_data)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

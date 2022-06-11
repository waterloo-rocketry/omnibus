import argparse
import serial

from omnibus import Sender
import parsley


def reader(port):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)

    def _reader():
        return s.readline().strip(b'\r\n').decode('utf-8')
    return _reader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--format', default='telemetry',
                        help='Options: telemetry, logger, usb. Parse input in RocketCAN Logger or USB format')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    readline = reader(args.port)
    parser = parsley.parse_live_telemetry
    if args.format == "usb":
        parser = parsley.parse_usb_debug
    elif args.format == "logger":
        parser = parsley.parse_logger
    if not args.solo:
        sender = Sender()
        CHANNEL = "CAN/Parsley"

    while True:
        line = readline()

        # treat repeated messages in the same way as USB debug
        if line.strip() == '.':
            print('.')
            continue

        try:
            msg_sid, msg_data = parser(line)
            parsed_data = parsley.parse(msg_sid, msg_data)

            print(parsley.fmt_line(parsed_data))
            if not args.solo:
                sender.send(CHANNEL, parsed_data)
        except Exception as e:
            print(e, line)
            pass


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

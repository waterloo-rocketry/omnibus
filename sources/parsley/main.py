import argparse
import serial

from omnibus import Sender, Receiver
import parsley
import sources.parsley.message_types as mt

def reader(port, baud):
    if port == "-":
        return input
    s = serial.Serial(port, baud, timeout=0) # non-blocking input

    def _reader():
        return s.readline().strip(b'\r\n').decode('utf-8')
    return _reader

    def write(self, msg):
        self.serial.write(msg)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('baud', type=int, nargs='?', default=115200,
                        help='the baud rate to use')
    parser.add_argument('--format', default='telemetry',
                        help='Options: telemetry, logger, usb. Parse input in RocketCAN Logger or USB format')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    communicator = SerialCommunicator(args.port, args.baud, 0)
    parser = parsley.parse_live_telemetry
    if args.format == "usb":
        parser = parsley.parse_usb_debug
    elif args.format == "logger":
        parser = parsley.parse_logger
    else:
        parser = parsley.parse_live_telemetry

    if not args.solo:
        sender = Sender()
        CHANNEL = "CAN/Parsley"

    receiver = Receiver("CAN/Commands")

    while True:
        while msg := receiver.recv_message(0):
            print(msg.payload['message'])
            msg_sid, msg_data = msg.payload['message']
            print(f"{msg_sid} => {mt.msg_type_str[msg_sid]}")

        line = readline()
        if not line:
            continue

    while True:
        while msg := receiver.recv_message(0):
            msg_sid, msg_data = msg.payload['message']
            # print(parsley.parse(msg_sid, msg_data))
            # communicator.write(msg_sid | msg_data)

        line = communicator.read()
        if not line:
            continue

        try:
            msg_sid, msg_data = parser(line)
            parsed_data = parsley.parse(msg_sid, msg_data)

            print(parsley.format_line(parsed_data))
            if not args.solo:
                sender.send(CHANNEL, parsed_data)
        except Exception:
            print(line)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

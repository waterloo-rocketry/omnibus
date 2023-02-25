import argparse
import serial

from omnibus import Sender, Receiver
import parsley
import sources.parsley.message_types as mt

class SerialCommunicator:
    def __init__(self, port, baud, timeout):
        self.port = port
        if self.port == "-":
            return
        self.serial = serial.Serial(port, baud, timeout=timeout)

    def read(self):
        if self.port == "-":
            return input()
        return self.serial.readline().strip(b'\r\n').decode('utf-8')

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
    if not args.solo:
        sender = Sender()
        CHANNEL = "CAN/Parsley"

    receiver = Receiver("CAN/Commands")

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

            print(parsley.fmt_line(parsed_data))
            if not args.solo:
                sender.send(CHANNEL, parsed_data)
        except Exception as e:
            print(line)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

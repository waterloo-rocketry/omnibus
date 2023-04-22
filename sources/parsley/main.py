import argparse
import serial

from omnibus import Sender, Receiver
import parsley

class SerialCommunicator:
    def __init__(self, port, baud, timeout):
        self.port = port
        self.serial = None
        if self.port != "-":
            self.serial = serial.Serial(port, baud, timeout)

    def read(self):
        if self.serial == None:
            return input
        return self.serial.readline().strip(b'\r\n').decode('utf-8')

    def write(self, msg):
        if self.serial == None:
            print(msg)
            return
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
            data = msg.payload['data']
            length = msg.payload['length']
            bit_str = parsley.BitString(data, length)
            msg_sid, msg_data = parsley.parse_bitstring(bit_str)
            formatted_msg_sid = f"{msg_sid:03X}"
            byte_length = (length-11 + 7) // 8  # calculate the number of bytes required
            byte_array = msg_data.to_bytes(byte_length, byteorder='big')  # convert to bytes
            formatted_msg_data = ','.join([f"{byte:02X}" for byte in byte_array])  # convert to hex with commas
            formatted_string = f"m{formatted_msg_sid},{formatted_msg_data};"
            communicator.write(formatted_string)

        line = communicator.read()
        if line is not None or line is input:
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

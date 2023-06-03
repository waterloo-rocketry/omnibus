import argparse
import time
import serial
from socket import gethostname

from omnibus import Sender, Receiver
import parsley

SEND_CHANNEL = "CAN/Parsley"
RECEIVE_CHANNEL = "CAN/Commands"
HEARTBEAT_CHANNEL = "Parsley/Health"


class SerialCommunicator:
    def __init__(self, port, baud, timeout):
        self.port = port
        self.serial = serial.Serial(port, baud, timeout=timeout)

    def read(self):
        return self.serial.read(4096).decode('utf-8')

    def write(self, msg):
        self.serial.write(msg)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from')
    parser.add_argument('baud', type=int, nargs='?', default=115200,
                        help='the baud rate to use')
    parser.add_argument('--format', default='usb',
                        help='Options: telemetry, logger, usb. Parse input in RocketCAN Logger or USB format')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    communicator = SerialCommunicator(args.port, args.baud, 0)
    if args.format == "telemetry":
        parser = parsley.parse_live_telemetry
    elif args.format == "logger":
        parser = parsley.parse_logger
    else:
        parser = parsley.parse_usb_debug

    sender = None
    receiver = None
    if not args.solo:
        sender = Sender()
        receiver = Receiver(RECEIVE_CHANNEL)

    last_valid_message_time = 0
    last_heartbeat_time = time.time()

    # invariant - buffer starts with the start of a message
    buffer = ""
    while True:
        if sender and time.time() - last_heartbeat_time > 1:
            last_heartbeat_time = time.time()
            healthy = "Healthy" if time.time() - last_valid_message_time < 1 else "Dead"
            sender.send(HEARTBEAT_CHANNEL, {"id": f"{gethostname()}/{args.format}", "healthy": healthy})

        if receiver and (msg := receiver.recv_message(0)):  # non-blocking
            can_msg_data = msg.payload['data']['can_msg']
            msg_sid, msg_data = parsley.encode_data(can_msg_data)

            formatted_msg_sid = f"{msg_sid:03X}"
            formatted_msg_data = ','.join([f"{byte:02X}" for byte in msg_data])
            formatted_string = str.encode(f"m{formatted_msg_sid},{formatted_msg_data};  \n")
            print(formatted_string)  # always print the usb debug style can message
            if not args.solo:
                communicator.write(formatted_string)  # send the can message over the specified port
            time.sleep(0.01)

        line = communicator.read()
        if not line or line.encode() == b'\x00':
            time.sleep(0.01)
            continue

        while '\n' in line:
            i = line.find('\n')
            msg = buffer + line[:i]
            buffer = ""
            line = line[i+1:]

            msg = msg.strip('\x00\r')

            try:
                msg_sid, msg_data = parser(msg)
                parsed_data = parsley.parse(msg_sid, msg_data)

                last_valid_message_time = time.time()

                print(parsley.format_line(parsed_data))
                if sender:
                    sender.send(SEND_CHANNEL, parsed_data)  # send the CAN message over the channel
            except Exception:
                print(msg.encode())
                pass

        buffer += line


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

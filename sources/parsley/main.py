import argparse
import time
import serial
import crc8
from socket import gethostname
import traceback
import random

from omnibus import Sender, Receiver
import parsley

from omnibus.omnibus import Message

SEND_CHANNEL = "CAN/Parsley"
# Note: The Receiver will also listen on the HEARTBEAT_CHANNEL to make sure that it is still alive
RECEIVE_CHANNEL = "CAN/Commands"
HEARTBEAT_CHANNEL = "Parsley/Health"

HEARTBEAT_TIME = 1
KEEPALIVE_TIME = 10
FAKE_MESSAGE_SPACING = 0.2


class SerialCommunicator:
    def __init__(self, port: str, baud: int, timeout: int):
        self.port = port
        self.serial = serial.Serial(port, baud, timeout=timeout)

    def read(self):
        return self.serial.read(4096)

    def write(self, msg: bytes):
        self.serial.write(msg)

class FileCommunicator:
    def __init__(self, filename: str):
        self.file = open(filename, mode='rb')
        self.page_size = 4096
        self.page_number = 0

    def read(self):
        if self.file.closed:
            return b""
        self.file.seek(self.page_number * self.page_size)
        data = self.file.read(self.page_size)
        if data:
            self.page_number += 1 # Increment page number after reading
        else:
            self.file.close()
        return data

    def write(self, msg: bytes):
        print('Cannot write to file: {msg}')

# Acting as a fake usb debug board
class FakeSerialCommunicator:
    def __init__(self):
        # Fake messages to cycle through
        self.fake_msgs = [
            {
                "board_type_id": "INJ_SENSOR",
                "board_inst_id": "GENERIC",
                "msg_prio": "HIGH",
                "msg_type": "SENSOR_ANALOG",
                "time": 1234,
                "sensor_id": "SENSOR_PRESSURE_CC",
                "value": 800,
            },
        ]
        self.fake_msg_index = 0
        self.last_fake_zero_time = 0
        self.zero_time = time.time()

    def read(self):
        now = time.time()
        if now - self.last_fake_zero_time > FAKE_MESSAGE_SPACING:
            # Time is in seconds, mod 65536ms to get the 16 bit time
            self.fake_msgs[self.fake_msg_index]["time"] = (
                ((now - self.zero_time) * 1000) % 65536
            ) / 1000
            if "value" in self.fake_msgs[self.fake_msg_index]:
                self.fake_msgs[self.fake_msg_index]["value"] = random.randint(0, 10)

            # Turn the fake message from the dict to the bytes representation that would be read from the serial connection, like from the USB debug board
            msg_sid, msg_data = parsley.encode_data(self.fake_msgs[self.fake_msg_index])
            formatted_msg = f"{msg_sid:03X}"
            if msg_data:
                formatted_msg += ":" + ",".join(
                    f"{byte:02X}" for byte in msg_data
                )  # Debug messages have a colon between the sid and data, see https://github.com/waterloo-rocketry/cansw_usb/blob/1575995e9364bca99443362ff51a5311a8a10174/usb_app.c#L99
            formatted_msg = f"${formatted_msg} \0\r\n"

            # Update the index after encoding
            self.fake_msg_index = (self.fake_msg_index + 1) % len(self.fake_msgs)
            if self.fake_msg_index == 0:
                self.last_fake_zero_time = now

            return formatted_msg.encode(encoding="utf-8")
        else:
            return b""

    def write(self, msg):
        print(f"Fake serial write out: {msg}")


def receive_commands(
    receiver: Receiver | None,
    sender_id: str,
    communicator: SerialCommunicator | FakeSerialCommunicator | FileCommunicator,
) -> bool:  # True on received, false otherwise

    if not receiver:
        return False

    msg: Message | None = receiver.recv_message(0)  # Non-blocking
    if not msg or msg.channel != RECEIVE_CHANNEL:
        return False

    can_msg_data = msg.payload["data"]["can_msg"]
    msg_sid, msg_data = parsley.encode_data(can_msg_data)

    # Checking parsley instance
    parsley_instance = msg.payload["parsley"]
    if parsley_instance != sender_id:
        return False

    formatted_msg = f"m{msg_sid:08X}"
    if msg_data:
        formatted_msg += "," + ",".join(f"{byte:02X}" for byte in msg_data)

    # Sent messages in the usb debug format have a crc8 checksum at the end, to be investigated:
    # https://github.com/waterloo-rocketry/omnibus/commit/0913ff2ef1c38c3ae715ad87c805d071c1ce2c38
    formatted_msg += (
        ";"
        + crc8.crc8(msg_sid.to_bytes(4, byteorder="big") + bytes(msg_data))
        .hexdigest()
        .upper()
    )
    print(formatted_msg)  # Always print the usb debug style can message
    # Send the can message over the specified port
    communicator.write(formatted_msg.encode())
    return True


def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument(
        "port_or_file",
        type=str,
        nargs="?",
        default="FAKEPORT",
        help="the serial port to read from, not needed for fake mode",
    )
    argparser.add_argument(
        "baud", type=int, nargs="?", default=115200, help="the baud rate to use"
    )
    argparser.add_argument(
        "--format",
        default="usb",
        help="Options: telemetry, logger, usb. Parse input in RocketCAN Logger or USB format",
    )
    argparser.add_argument(
        "--solo",
        action="store_true",
        help="Don't connect to omnibus - just print to stdout.",
    )
    argparser.add_argument(
        "--fake",
        action="store_true",
        help="Don't read from hardware - uses fake data. Give any value for a port",
    )
    argparser.add_argument(
        "--file",
        action="store_true",
        help="Don't read from hardware - read from a file instead",
    )
    args = argparser.parse_args()

    if args.fake:
        if args.format != "usb":
            print("Fake mode only supports usb format")
            exit(1)
        communicator = FakeSerialCommunicator()
    elif args.file:
        if args.format != "logger":
            print("File mode only supports logger format")
            exit(1)
        communicator = FileCommunicator(args.port_or_file)
    else:
        if args.port_or_file == "FAKEPORT":
            print("Please specify a serial port by name or use --fake")
            exit(1)
        communicator = SerialCommunicator(args.port_or_file, args.baud, 0)

    if args.format == "telemetry":
        parser = parsley.parse_live_telemetry
    elif args.format == "logger":
        parser = parsley.parse_logger
    else:
        parser = parsley.parse_usb_debug

    sender_id = f"{gethostname()}/{args.format}/{args.port_or_file}"

    if args.solo:
        sender = None
        receiver = None
    elif args.fake:
        print("Parsley started in fake mode")
        sender = Sender()
        receiver = Receiver(RECEIVE_CHANNEL, HEARTBEAT_CHANNEL)
    else:
        sender = Sender()
        receiver = Receiver(RECEIVE_CHANNEL, HEARTBEAT_CHANNEL)

    last_valid_message_time = 0
    last_heartbeat_time = time.time()
    last_keepalive_time = 0

    # Invariant - buffer starts with the start of a message
    buffer = b""
    while True:
        now = time.time()

        if sender and now - last_heartbeat_time > HEARTBEAT_TIME:
            last_heartbeat_time = now
            healthy = "Healthy" if time.time() - last_valid_message_time < 1 else "Dead"
            sender.send(HEARTBEAT_CHANNEL, {"id": sender_id, "healthy": healthy})

        if (
            args.format == "telemetry"
            and time.time() - last_keepalive_time > KEEPALIVE_TIME
        ):
            communicator.write(b".")
            last_keepalive_time = now

        command_was_received: bool = receive_commands(receiver, sender_id, communicator)
        if command_was_received:
            last_keepalive_time: float = now
            time.sleep(0.01)

        line = communicator.read()

        if not line:
            time.sleep(0.01)
            continue

        buffer += line

        while True:
            try:
                if args.format == "telemetry":
                    i = next((i for i, b in enumerate(buffer) if b == 0x02), -1)
                    if i < 0 or i + 1 >= len(buffer):
                        break
                    msg_len = buffer[i + 1]
                    if i + msg_len > len(buffer):
                        break
                    msg = buffer[i : i + msg_len]
                    try:
                        msg_sid, msg_data = parser(msg)
                        buffer = buffer[i + msg_len :]
                    except ValueError as e:
                        buffer = buffer[i + 1 :]
                        raise e
                elif args.format == "logger":
                    msg_sid, msg_data = parser(buffer, communicator.page_number - 1)
                else:
                    text_buff = buffer.decode("utf-8", errors="backslashreplace")
                    i = text_buff.find("\n")
                    if i < 0:
                        break
                    msg = text_buff[:i]
                    buffer = buffer[i + 1 :]
                    msg_sid, msg_data = parser(msg)

                parsed_data = parsley.parse(msg_sid, msg_data)
                last_valid_message_time = time.time()
                print(parsley.format_line(parsed_data))
                
                # Send the CAN message over the channel
                if sender:
                    sender.send(channel=SEND_CHANNEL, payload=parsed_data)

                if args.format == "logger":
                    buffer = b""  # Reset buffer after processing a logger message
                    break

            except ValueError as e:
                print(e)
                print(msg.hex() if args.format == "telemetry" else msg)
            except Exception:
                print(traceback.format_exc())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

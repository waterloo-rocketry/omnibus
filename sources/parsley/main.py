import argparse
import time
import serial
import crc8
from socket import gethostname
import traceback
import random

from omnibus import Sender, Receiver
import parsley

SEND_CHANNEL = "CAN/Parsley"
RECEIVE_CHANNEL = "CAN/Commands"
HEARTBEAT_CHANNEL = "Parsley/Health"

HEARTBEAT_TIME = 1
KEEPALIVE_TIME = 10
FAKE_MESSAGE_SPACING = 0.25


class SerialCommunicator:
    def __init__(self, port, baud, timeout):
        self.port = port
        self.serial = serial.Serial(port, baud, timeout=timeout)

    def read(self):
        return self.serial.read(4096)

    def write(self, msg):
        self.serial.write(msg)

class FakeSerialCommunicator:
    def __init__(self):
        # fake messages to cycle through
        self.fake_msgs = [
            {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_BATT_CURR', 'value': 0},
            {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_BUS_CURR', 'value': 0},
            {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_CHARGE_CURR', 'value': 0},
            {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_BATT_VOLT', 'value': 0},
            {'board_id': 'CHARGING', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_GROUND_VOLT', 'value': 0},
            {'board_id': 'ACTUATOR_INJ', 'msg_type': 'SENSOR_ANALOG', 'time': 0, 'sensor_id': 'SENSOR_BATT_VOLT', 'value': 0},
            {'board_id': 'ACTUATOR_INJ', 'msg_type': 'GENERAL_BOARD_STATUS', 'time': 0, 'status': 'E_NOMINAL'},
            {'board_id': 'ACTUATOR_INJ', 'msg_type': 'ACTUATOR_STATUS', 'time': 0, 'actuator': 'ACTUATOR_INJECTOR_VALVE', 'req_state': 'ACTUATOR_UNK', 'cur_state': 'ACTUATOR_OFF'},
            {'board_id': 'CHARGING', 'msg_type': 'GENERAL_BOARD_STATUS', 'time': 0, 'status': 'E_NOMINAL'},
        ]
        self.fake_msg_index = 0
        self.last_fake_zero_time = 0
        self.zero_time = time.time()


    def read(self):
        now = time.time()
        if now - self.last_fake_zero_time > FAKE_MESSAGE_SPACING:
            self.fake_msgs[self.fake_msg_index]['time'] = now - self.zero_time
            if "value" in self.fake_msgs[self.fake_msg_index]:
                self.fake_msgs[self.fake_msg_index]["value"] = random.randint(0, 10)

            # turn the fake message from the dict to the bytes representation that would be read from the serial connection
            # print(self.fake_msg_index, self.fake_msgs[self.fake_msg_index])
            formatted_msg = prepCanMessage(self.fake_msgs[self.fake_msg_index])

            # update the index after encoding
            self.fake_msg_index = (self.fake_msg_index + 1) % len(self.fake_msgs)
            if self.fake_msg_index == 0:
                self.last_fake_zero_time = now

            formatted_msg += '\n'

            return formatted_msg.encode(encoding='utf-8')
            # FIXME: this doesnt correctly encode the message, i'm getting Incorrect line format when I add a \n, or it's just never decoding anything if i dont add the \n
            # It would be good to have an example of how the real devices encode the data, or closer to real so that we can match the template
        
            # also just lost on what formats are for what, they all give different errors. logger gives
            # m6A1,1B,14,02,00,09;69
            # invalid literal for int() with base 16: 'm52'
            # m521,00,1B,14,00;C6
            # invalid literal for int() with base 16: 'm46'
            # m461,00,1B,14,01,01,02;B5
            # invalid literal for int() with base 16: 'm52'
        
            # Ex if i add \n at the end in default format: Incorrect line format
            # m461,00,07,EC,01,01,02;A2
            # m52E,00,07,EC,00;12
            # Incorrect line format
            # m52E,00,07,EC,00;12
        
            # Ex: telemetry mode passes through a bit, but then can't find the 0x02 in this line       i = next((i for i, b in enumerate(buffer) if b == 0x02), -1) and gets -1
        
            # so what's the correct way to format it? currently my output is Buffer: b'm6AE,00,C0,01,00,01;64\n'

        else:
            return b''

    def write(self,msg):
        print(f"Fake serial write out: {msg}")


def prepCanMessage(can_msg_data):
    msg_sid, msg_data = parsley.encode_data(can_msg_data)
    formatted_msg = f"m{msg_sid:03X}"
    if msg_data:
        formatted_msg += ',' + ','.join(f"{byte:02X}" for byte in msg_data)
    formatted_msg += ";" + crc8.crc8(
        msg_sid.to_bytes(2, byteorder='big') + bytes(msg_data)
    ).hexdigest().upper()
    return formatted_msg

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('port', help='the serial port to read from')
    argparser.add_argument('baud', type=int, nargs='?', default=115200,
                        help='the baud rate to use')
    argparser.add_argument('--format', default='usb',
                        help='Options: telemetry, logger, usb. Parse input in RocketCAN Logger or USB format')
    argparser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    argparser.add_argument('--fake', action='store_true',
                        help="Don't read from hardware - uses fake data. Give any value for a port")
    args = argparser.parse_args()

    if not args.fake:
        communicator = SerialCommunicator(args.port, args.baud, 0)
    else:
        communicator = FakeSerialCommunicator()
    
    parser = parsley.parse_usb_debug
    if args.format == "telemetry":
        parser = parsley.parse_live_telemetry
    elif args.format == "logger":
        parser = parsley.parse_logger

    if args.format == "telemetry":
        channel = "telemetry/" + RECEIVE_CHANNEL
    else:
        channel = RECEIVE_CHANNEL

    if args.solo:
        sender = None
        receiver = None
    elif args.fake:
        print("Parsley started in fake mode")
        sender = Sender()
        receiver = None # we do not receive instructions that we need to repeat in fake mode
    else:
        sender = Sender()
        receiver = Receiver(channel)

    last_valid_message_time = 0
    last_heartbeat_time = time.time()
    last_keepalive_time = 0

    # invariant - buffer starts with the start of a message
    buffer = b''
    while True:
        now = time.time()

        if sender and now - last_heartbeat_time > HEARTBEAT_TIME:
            last_heartbeat_time = now
            healthy = "Healthy" if time.time() - last_valid_message_time < 1 else "Dead"
            sender.send(HEARTBEAT_CHANNEL, {
                "id": f"{gethostname()}/{args.format}", "healthy": healthy})

        if args.format == "telemetry" and time.time() - last_keepalive_time > KEEPALIVE_TIME:
            communicator.write(b'.')
            last_keepalive_time = now

        if receiver and (msg := receiver.recv_message(0)):  # non-blocking
            can_msg_data = msg.payload['data']['can_msg']
            formatted_msg = prepCanMessage(can_msg_data)
            print(formatted_msg)  # always print the usb debug style can message
            # send the can message over the specified port
            communicator.write(formatted_msg.encode())
            last_keepalive_time = now
            time.sleep(0.01)

        line = communicator.read()
        # print(f"Read in: {line}")

        if not line:
            time.sleep(0.01)
            continue

        buffer += line

        while True:
            print(f"Buffer: {buffer}")
            try:
                if args.format == "telemetry":
                    i = next((i for i, b in enumerate(buffer) if b == 0x02), -1)
                    print(f"i: {i}")
                    if i < 0 or i + 1 >= len(buffer):
                        break
                    msg_len = buffer[i+1] >> 4
                    if i + msg_len > len(buffer):
                        break
                    msg = buffer[i:i+msg_len]
                    print(f"Telemetry buffer: {msg}")
                    try:
                        msg_sid, msg_data = parser(msg)
                        buffer = buffer[i+msg_len:]
                    except ValueError as e:
                        buffer = buffer[i+1:]
                        raise e
                else:
                    text_buff = buffer.decode('utf-8', errors='backslashreplace')
                    i = text_buff.find('\n')
                    if i < 0:
                        break
                    msg = text_buff[:i]
                    buffer = buffer[i+1:]
                    # print(f"Text buffer: {msg}")
                    msg_sid, msg_data = parser(msg)
                
                parsed_data = parsley.parse(msg_sid, msg_data)
                last_valid_message_time = time.time()
                print(parsley.format_line(parsed_data))

                if sender:
                    sender.send(SEND_CHANNEL, parsed_data)  # send the CAN message over the channel

            except ValueError as e:
                print(e)
                print(msg.hex() if args.format == "telemetry" else msg)
            except Exception:
                print(traceback.format_exc())


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

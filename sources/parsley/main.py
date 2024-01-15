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

class FakeSerialCommunicator: # acting as a fake usb debug board
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

            # turn the fake message from the dict to the bytes representation that would be read from the serial connection, like from the USB debug board
            msg_sid, msg_data = parsley.encode_data(self.fake_msgs[self.fake_msg_index])
            formatted_msg = f"{msg_sid:03X}"
            if msg_data:
                formatted_msg += ':' + ','.join(f"{byte:02X}" for byte in msg_data) # debug messages have a colon between the sid and data, see https://github.com/waterloo-rocketry/cansw_usb/blob/1575995e9364bca99443362ff51a5311a8a10174/usb_app.c#L99
            formatted_msg = f"${formatted_msg} \0\r\n"

            # update the index after encoding
            self.fake_msg_index = (self.fake_msg_index + 1) % len(self.fake_msgs)
            if self.fake_msg_index == 0:
                self.last_fake_zero_time = now

            return formatted_msg.encode(encoding='utf-8')
        else:
            return b''

    def write(self,msg):
        print(f"Fake serial write out: {msg}")

def main():
    argparser = argparse.ArgumentParser()
    argparser.add_argument('port', type=str, nargs='?', default="NOPORT", help='the serial port to read from, not needed for fake mode')
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
        if args.port == "NOPORT":
            print("Please specify a serial port by name or use --fake")
            exit(1)
        communicator = SerialCommunicator(args.port, args.baud, 0)
    else:
        if args.format != "usb":
            print("Fake mode only supports usb format")
            exit(1)
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
            msg_sid, msg_data = parsley.encode_data(can_msg_data)
            formatted_msg = f"m{msg_sid:03X}"
            if msg_data:
                formatted_msg += ',' + ','.join(f"{byte:02X}" for byte in msg_data)
            formatted_msg += ";" + crc8.crc8(
                msg_sid.to_bytes(2, byteorder='big') + bytes(msg_data)
            ).hexdigest().upper() # sent messages in the usb debug format have a crc8 checksum at the end, to be investigated: https://github.com/waterloo-rocketry/omnibus/commit/0913ff2ef1c38c3ae715ad87c805d071c1ce2c38 
            print(formatted_msg)  # always print the usb debug style can message
            # send the can message over the specified port
            communicator.write(formatted_msg.encode())
            last_keepalive_time = now
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
                    msg_len = buffer[i+1] >> 4
                    if i + msg_len > len(buffer):
                        break
                    msg = buffer[i:i+msg_len]
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

import argparse
import serial

from omnibus import Sender

import rlcs
import time


msg_index = [
    "rlcs_main_batt_mv",
    "rlcs_actuator_batt_mv",
    "healthy_actuators",
    "ignition_primary_ma",
    "ignition_primary_ma",
    "fill_valve_state",
    "vent_valve_state",
    "injector_valve_state"
]


def parse_rlcs(line):
    res = {}
    # timestamp and msg_type
    res["msg_type"] = "rlcs"
    res["timestamp"] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
    res["data"] = {}
    # items
    for i,s in enumerate(msg_index):
        res["data"][s] = int(line[4*i:4*i+4], base=16) # 4 chars for each keyword
    return res


def reader(port):
    if port == "-":
        return input
    s = serial.Serial(port, 9600) # this is just copied from parsley, change if needed

    def _reader():
        return s.readline().strip(b'\r\n').decode('utf-8')
    return _reader


def generate_line():
    """
        Dummy function to generate a (soon-to-be) random line of valid RLCS-format input data
        W[xxxx][xxxx]...[xxxx]R where xxxx = a hexadecimal number
    """
    from random import random

    line = "W"

    for _ in range(8):
        hexnum = hex(int(random()*65536))[2:6]
        h = hexnum.rjust(4, '0')
        line += h
        print(h)

    line = line + "R"
    return line


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--format', default='usb',
                        help='Options: logger, usb. Parse input in RocketCAN Logger or USB format')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    args = parser.parse_args()

    readline = reader(args.port)
    # parser = parsley.parse_logger if args.format == 'logger' else parsley.parse_usb_debug
    if not args.solo:
        sender = Sender()
        CHANNEL = "CAN/RLCS"

    while True:
        line = readline()
        # line = generate_line()
        if not line:
            break

        # check if line is in a valid input format
        if line[0] != "W" or line[len(line)-1] != "R":
            print("Data " + line + " is invalid (must end with R and begin with W")
            time.sleep(5)
            continue # do we want to throw or use continue?
        
        if len(line) > 34 or len(line) < 34:
            print("Warning: Format {} is wrong".format(line))
            time.sleep(5)
            continue # far future possibly
        
        if len(line) == 34:
            stripped_data = line[1:len(line)-1]
            parsed_data = parse_rlcs(stripped_data)

        print(rlcs.fmt_line(parsed_data)) # print debug code 
        time.sleep(5)

        if not args.solo: # if connect to omnibus
            sender.send(CHANNEL, parsed_data)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass

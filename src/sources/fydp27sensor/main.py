import argparse
import serial
import time

from omnibus import Sender

def reader(port: str):
    if port == "-":
        return input
    s = serial.Serial(port, 115200)  # listen on the RLCS port

    def _reader():
        while True:
            c = s.read()
            if c != b'F':
                continue

            output = b'F' + s.read(7 + 1) # Data + 'R'

            if output[-1] != ord('S'):
                print(f"Incorrectly terminated FYDP27SENSOR message: {[c for c in output]}")
                continue

            return output

    return _reader

def parse_fydp27sensor(line: str | bytes) -> dict[str, str] | None:
    res = {}

    res['rpm'] = (line[2] << 8 | line[1]) * 10
    res['battery_voltage'] = (line[4] << 8 | line[3]) / 10
    res['current'] = (line[6] << 8 | line[5]) / 10
    res['esc_temp'] = line[7] - 20
        
    return res

def fake_parse_fydp27sensor() -> dict[str, str] | None:
    res = {}

    res['rpm'] = 12345
    res['battery_voltage'] = 12.34
    res['current'] = 234
    res['esc_temp'] = 25
    res['max_accel'] = 67

    return res

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('port', help='the serial port to read from, or - for stdin')
    parser.add_argument('--solo', action='store_true',
                        help="Don't connect to omnibus - just print to stdout.")
    parser.add_argument('--fake', action="store_true",
                        help="Don't read from hardware - uses fake data. Give any value for a port")
    args = parser.parse_args()

    if not args.fake:
        readline = reader(args.port)

    if not args.solo:
        sender = Sender()
        CHANNEL = "FYDP27SENSOR"

    while True:
        if not args.fake:
            line = readline()
            if not len(line):
                continue
            parsed_data = parse_fydp27sensor(line)
        else:
            time.sleep(0.1)
            parsed_data = fake_parse_fydp27sensor()

        if not parsed_data:
            continue

        if not args.solo:  # if connect to omnibus
            sender.send(CHANNEL, parsed_data)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
